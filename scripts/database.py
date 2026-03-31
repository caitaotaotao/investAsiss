#!/usr/bin/env python3
"""
远程数据库连接工具 — 通过 SSH 隧道安全访问远程数据库。

支持：
  - SSH 隧道（密码 / 密钥认证）
  - MySQL / PostgreSQL 数据库
  - 连接池管理
  - CLI 快速查询

用法：
  # 交互式查询（使用 .env 中的默认配置）
  python scripts/database.py query "SELECT * FROM table LIMIT 10"

  # 指定输出格式
  python scripts/database.py query "SELECT * FROM table" --format json
  python scripts/database.py query "SELECT * FROM table" --format csv

  # 测试连接
  python scripts/database.py test

  # 列出所有表
  python scripts/database.py tables

环境变量（在 .env 中配置）：
  SSH_HOST        - SSH 服务器地址
  SSH_PORT        - SSH 端口（默认 22）
  SSH_USER        - SSH 用户名
  SSH_PASSWORD    - SSH 密码（与 SSH_KEY_PATH 二选一）
  SSH_KEY_PATH    - SSH 私钥路径（与 SSH_PASSWORD 二选一）
  DB_TYPE         - 数据库类型: mysql / postgresql（默认 mysql）
  DB_HOST         - 数据库地址（远程机器上的地址，默认 127.0.0.1）
  DB_PORT         - 数据库端口（MySQL 默认 3306，PostgreSQL 默认 5432）
  DB_USER         - 数据库用户名
  DB_PASSWORD     - 数据库密码
  DB_NAME         - 数据库名称
"""

import argparse
import csv
import io
import json
import logging
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from sshtunnel import SSHTunnelForwarder
except ImportError:
    print("Error: sshtunnel 未安装，请执行: pip install sshtunnel", file=sys.stderr)
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.pool import QueuePool
except ImportError:
    print("Error: sqlalchemy 未安装，请执行: pip install sqlalchemy", file=sys.stderr)
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)

DEFAULT_DB_PORTS = {
    "mysql": 3306,
    "postgresql": 5432,
}

DRIVER_MAP = {
    "mysql": "mysql+pymysql",
    "postgresql": "postgresql+psycopg2",
}


@dataclass
class SSHConfig:
    """SSH 连接配置。"""
    host: str
    port: int = 22
    user: str = ""
    password: Optional[str] = None
    key_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SSHConfig":
        """从环境变量加载 SSH 配置。"""
        host = os.getenv("SSH_HOST", "")
        if not host:
            raise ValueError("SSH_HOST 未配置")
        return cls(
            host=host,
            port=int(os.getenv("SSH_PORT", "22")),
            user=os.getenv("SSH_USER", ""),
            password=os.getenv("SSH_PASSWORD"),
            key_path=os.getenv("SSH_KEY_PATH"),
        )


@dataclass
class DBConfig:
    """数据库连接配置。"""
    db_type: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""

    @classmethod
    def from_env(cls) -> "DBConfig":
        """从环境变量加载数据库配置。"""
        db_type = os.getenv("DB_TYPE", "mysql").lower()
        default_port = DEFAULT_DB_PORTS.get(db_type, 3306)
        return cls(
            db_type=db_type,
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", str(default_port))),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
        )

    @property
    def driver(self) -> str:
        driver = DRIVER_MAP.get(self.db_type)
        if not driver:
            raise ValueError(f"不支持的数据库类型: {self.db_type}，支持: {list(DRIVER_MAP.keys())}")
        return driver


class DatabaseClient:
    """通过 SSH 隧道连接远程数据库的客户端。

    支持作为上下文管理器使用，自动管理 SSH 隧道和数据库连接的生命周期。

    Example:
        >>> with DatabaseClient() as db:
        ...     results = db.query("SELECT * FROM users LIMIT 5")
        ...     for row in results:
        ...         print(row)
    """

    def __init__(
        self,
        ssh_config: Optional[SSHConfig] = None,
        db_config: Optional[DBConfig] = None,
    ):
        self._ssh_config = ssh_config
        self._db_config = db_config
        self._tunnel: Optional[SSHTunnelForwarder] = None
        self._engine: Optional[Engine] = None

    def _load_env(self) -> None:
        if load_dotenv is not None:
            env_path = Path(__file__).resolve().parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)

    def _ensure_configs(self) -> Tuple[SSHConfig, DBConfig]:
        self._load_env()
        ssh = self._ssh_config or SSHConfig.from_env()
        db = self._db_config or DBConfig.from_env()
        return ssh, db

    def connect(self) -> None:
        """建立 SSH 隧道和数据库连接。"""
        if self._engine is not None:
            return

        ssh, db = self._ensure_configs()

        ssh_kwargs: Dict[str, Any] = {
            "ssh_address_or_host": (ssh.host, ssh.port),
            "ssh_username": ssh.user,
            "remote_bind_address": (db.host, db.port),
        }
        if ssh.key_path:
            ssh_kwargs["ssh_pkey"] = os.path.expanduser(ssh.key_path)
        if ssh.password:
            ssh_kwargs["ssh_password"] = ssh.password

        logger.info("正在建立 SSH 隧道: %s@%s:%d -> %s:%d",
                     ssh.user, ssh.host, ssh.port, db.host, db.port)

        self._tunnel = SSHTunnelForwarder(**ssh_kwargs)
        self._tunnel.start()

        local_port = self._tunnel.local_bind_port
        url = f"{db.driver}://{db.user}:{db.password}@127.0.0.1:{local_port}/{db.database}"

        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=3,
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        logger.info("数据库连接已建立 (本地端口: %d)", local_port)

    def close(self) -> None:
        """关闭数据库连接和 SSH 隧道。"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("数据库连接已关闭")

        if self._tunnel is not None:
            self._tunnel.stop()
            self._tunnel = None
            logger.info("SSH 隧道已关闭")

    def __enter__(self) -> "DatabaseClient":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _check_connected(self) -> Engine:
        if self._engine is None:
            raise RuntimeError("数据库未连接，请先调用 connect() 或使用 with 语句")
        return self._engine

    def query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行 SQL 查询并返回结果列表。

        Args:
            sql: SQL 查询语句
            params: SQL 参数（命名参数风格）

        Returns:
            结果列表，每行为一个字典。
        """
        engine = self._check_connected()
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """执行写操作（INSERT/UPDATE/DELETE）并返回受影响行数。

        Args:
            sql: SQL 语句
            params: SQL 参数

        Returns:
            受影响的行数。
        """
        engine = self._check_connected()
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            conn.commit()
            return result.rowcount

    def query_df(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行查询并返回 pandas DataFrame。

        Args:
            sql: SQL 查询语句
            params: SQL 参数

        Returns:
            pandas DataFrame（需要安装 pandas）。

        Raises:
            ImportError: 如果 pandas 未安装。
        """
        if pd is None:
            raise ImportError("pandas 未安装，请执行: pip install pandas")
        engine = self._check_connected()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)

    def list_tables(self) -> List[str]:
        """列出当前数据库中的所有表。"""
        engine = self._check_connected()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        return inspector.get_table_names()

    def table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取指定表的列信息。

        Args:
            table_name: 表名

        Returns:
            列信息列表。
        """
        engine = self._check_connected()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")),
            }
            for col in columns
        ]

    def test_connection(self) -> bool:
        """测试数据库连接是否正常。"""
        try:
            engine = self._check_connected()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("连接测试失败: %s", e)
            return False


@contextmanager
def get_db(
    ssh_config: Optional[SSHConfig] = None,
    db_config: Optional[DBConfig] = None,
) -> Generator[DatabaseClient, None, None]:
    """便捷的上下文管理器，用于获取数据库客户端。

    Example:
        >>> with get_db() as db:
        ...     rows = db.query("SELECT COUNT(*) as cnt FROM users")
    """
    client = DatabaseClient(ssh_config=ssh_config, db_config=db_config)
    try:
        client.connect()
        yield client
    finally:
        client.close()


def _format_results(rows: List[Dict[str, Any]], fmt: str = "table") -> str:
    """将查询结果格式化为指定格式。"""
    if not rows:
        return "(空结果集)"

    if fmt == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2, default=str)

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    # table format
    columns = list(rows[0].keys())
    col_widths = {col: len(str(col)) for col in columns}
    for row in rows:
        for col in columns:
            col_widths[col] = max(col_widths[col], len(str(row.get(col, ""))))

    header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)
    lines = [header, separator]
    for row in rows:
        line = " | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in columns)
        lines.append(line)

    lines.append(f"\n共 {len(rows)} 条记录")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="远程数据库连接工具 — 通过 SSH 隧道访问",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    query_parser = subparsers.add_parser("query", help="执行 SQL 查询")
    query_parser.add_argument("sql", help="SQL 查询语句")
    query_parser.add_argument(
        "--format", choices=["table", "json", "csv"], default="table",
        help="输出格式（默认 table）",
    )

    subparsers.add_parser("test", help="测试数据库连接")

    subparsers.add_parser("tables", help="列出所有表")

    info_parser = subparsers.add_parser("info", help="查看表结构")
    info_parser.add_argument("table", help="表名")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with get_db() as db:
        if args.command == "test":
            if db.test_connection():
                print("连接成功!")
                print(f"数据库表数量: {len(db.list_tables())}")
            else:
                print("连接失败!", file=sys.stderr)
                sys.exit(1)

        elif args.command == "tables":
            tables = db.list_tables()
            if tables:
                print(f"共 {len(tables)} 张表:\n")
                for i, t in enumerate(tables, 1):
                    print(f"  {i:3d}. {t}")
            else:
                print("当前数据库没有表")

        elif args.command == "info":
            columns = db.table_info(args.table)
            if columns:
                print(f"表 '{args.table}' 结构:\n")
                rows = [
                    {"列名": c["name"], "类型": c["type"],
                     "可空": "YES" if c["nullable"] else "NO",
                     "默认值": c["default"] or ""}
                    for c in columns
                ]
                print(_format_results(rows))
            else:
                print(f"表 '{args.table}' 不存在或没有列")

        elif args.command == "query":
            rows = db.query(args.sql)
            print(_format_results(rows, fmt=args.format))


if __name__ == "__main__":
    main()
