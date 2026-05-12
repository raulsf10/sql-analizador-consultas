from pydantic import BaseModel, Field, field_validator


_DIALECT_MAP: dict[str, str] = {
    "sqlserver": "tsql",
    "sql_server": "tsql",
    "mssql": "tsql",
    "t-sql": "tsql",
    "tsql": "tsql",
    "oracle": "oracle",
    "postgresql": "postgres",
    "postgres": "postgres",
    "mysql": "mysql",
}


class AnalyzeRequest(BaseModel):
    dialect: str = Field(
        default="tsql",
        description="SQL dialect: oracle | tsql | postgres | mysql",
    )
    script: str = Field(
        ...,
        description="SQL script to analyze (single or multiple statements)",
        min_length=1,
    )

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, v: str) -> str:
        mapped = _DIALECT_MAP.get(v.lower().strip())
        if mapped is None:
            raise ValueError(
                f"Unsupported dialect: '{v}'. Supported values: oracle, tsql (sql server), postgres, mysql"
            )
        return mapped

    @field_validator("script")
    @classmethod
    def validate_script(cls, v: str) -> str:
        v = v.strip().replace('\r\n', '\n').replace('\r', '\n')
        if not v:
            raise ValueError("SQL script cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"dialect": "oracle", "script": "DELETE FROM usuarios;"},
                {"dialect": "tsql", "script": "UPDATE clientes SET activo = 1;"},
                {"dialect": "postgres", "script": "SELECT * FROM pedidos;"},
            ]
        }
    }
