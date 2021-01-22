from enum import Enum
from typing import Union, Tuple


class ColumnType(Enum):
    STR = 1
    INT = 2
    FLOAT = 3


class QueryColumn:
    def __init__(
        self,
        name: str,
        col_type: ColumnType = None,
        table: str = None,
        alias: str = None,
    ):
        self.table = table
        self.name = name
        self.alias = alias
        self.col_type = col_type

    def to_query(self) -> Tuple[str, ColumnType]:
        s = ""
        if self.table is not None:
            s += f"{self.table}."
        s += f"{self.name}"

        if self.alias is not None:
            s += f" AS {self.alias}"

        return s, self.col_type

    def real_name(self) -> str:
        if self.alias is not None:
            return self.alias

        return self.original_name()

    def original_name(self) -> str:
        s = ""
        if self.table is not None:
            s += f"{self.table}."
        s += f"{self.name}"
        return s


class QueryJoin:
    def __init__(self, from_table: str, to_table: str, from_col: str, to_col: str):
        self.from_table = from_table
        self.to_table = to_table
        self.from_col = from_col
        self.to_col = to_col

    def __repr__(self) -> str:
        return f"""
JOIN {self.to_table}
ON {self.from_table}.{self.from_col} = {self.to_table}.{self.to_col}"""


QueryArg = Union[str, int, float, None]
QueryArgList = list[QueryArg]
QueryOptionArg = Tuple[str, QueryArgList]


class QueryOption:
    def __init__(self, table: str, column: str):
        self.table = table
        self.column = column

    def to_query(self) -> QueryOptionArg:
        return "", []


class QueryLikeOption(QueryOption):
    def __init__(self, table: str, column: str, like: str):
        super().__init__(table, column)
        self.like = like

    def to_query(self) -> QueryOptionArg:
        return f'{self.table}.{self.column} LIKE "%{self.like}%"', []


class QueryEqualOption(QueryOption):
    def __init__(self, table: str, column: str, equal: Union[str, int]):
        super().__init__(table, column)
        self.equal = equal

    def to_query(self) -> QueryOptionArg:
        return f"{self.table}.{self.column} = ?", [self.equal]


class QueryInfToOption(QueryOption):
    def __init__(self, table: str, column: str, inf: int):
        super().__init__(table, column)
        self.inf = inf

    def to_query(self) -> QueryOptionArg:
        return f"{self.table}.{self.column} < ?", [self.inf]


class QuerySupToOption(QueryOption):
    def __init__(self, table: str, column: str, sup: int):
        super().__init__(table, column)
        self.sup = sup

    def to_query(self) -> Tuple[str, Union[str, int, None]]:
        return f"{self.table}.{self.column} > ?", [self.sup]


class QueryNotEqualOption(QueryOption):
    def __init__(self, table: str, column: str, not_equal: Union[str, int]):
        super().__init__(table, column)
        self.not_equal = not_equal

    def to_query(self) -> Tuple[str, Union[str, int, None]]:
        return f"{self.table}.{self.column} > ?", [self.not_equal]


class QueryBetweenOption(QueryOption):
    def __init__(self, table: str, column: str, inf: int, sup: int):
        super().__init__(table, column)
        self.inf = inf
        self.sup = sup

    def to_query(self) -> Tuple[str, Union[str, int, None]]:
        return f"{self.table}.{self.column} BETWEEN ? AND ?", [self.inf, self.sup]


class QueryInOption(QueryOption):
    def __init__(
        self,
        table: str,
        column: str,
        args: Union[int, str] = [],
        col_type: ColumnType = ColumnType.INT,
    ):
        super().__init__(table, column)
        self.args = args
        self.col_type = col_type

    def to_query(self) -> Tuple[str, Union[str, int, None]]:
        s = f"{self.table}.{self.column} IN ("

        for e in self.args:
            s += "?,"

        s = s[:-1]
        s += ")"

        return s, self.args


class QueryNotInOption(QueryOption):
    def __init__(
        self,
        table: str,
        column: str,
        args: Union[int, str] = [],
        col_type: ColumnType = ColumnType.INT,
    ):
        super().__init__(table, column)
        self.args = args
        self.col_type = col_type

    def to_query(self) -> Tuple[str, Union[str, int, None]]:
        s = f"{self.table}.{self.column} NOT IN ("

        if self.col_type == ColumnType.INT:
            for e in self.args:
                s += f"{e},"
            s = s[:-1]

        else:
            for e in self.args:
                s += f"'{e}',"
            s = s[:-1]
            s += ")"

        return s, []


class Query:
    __db_table_join = {
        "genres": [
            QueryJoin("library", "genre_list", "id", "library_id"),
            QueryJoin("genre_list", "genres", "genre_id", "id"),
        ]
    }

    def __init__(
        self,
        columns: list[QueryColumn] = [],
        table: str = "library",
        limit: int = -1,
        order_by: list[QueryColumn] = [],
        order_by_random: bool = False,
        group_by: list[QueryColumn] = [],
    ):
        self.cte: list[Tuple[Query, str]] = []
        self.columns = columns
        self.joins: list[QueryJoin] = []
        self.options: list[QueryOption] = []
        self.tables: list[str] = [table]
        self.limit = limit
        self.order_by = order_by
        self.group_by = group_by
        self.order_by_random = order_by_random

    def __repr__(self) -> str:
        return ""

    def add_option(self, option: QueryOption) -> None:
        self.options.append(option)
        self.add_table(option.table)

    def add_table(self, table: str) -> None:
        if (
            table not in self.tables
            and table not in [name for _, name in self.cte]
            and table in self.__db_table_join
        ):
            self.tables.append(table)
            self.joins += self.__db_table_join[table]

    def add_join(self, join: QueryJoin) -> None:
        self.joins.append(join)

    def add_with(self, with_query, as_name: str) -> None:
        self.cte.append((with_query, as_name))

    def to_query(self) -> QueryOptionArg:
        args = []
        s = ""
        columns = []

        if len(self.cte) > 0:
            s += "WITH "
            for q, name in self.cte:
                s += "(" + q.to_query() + f") AS {name},\n"
            s = s[:-2] + "\n"

        select = ""

        if len(self.columns) > 0:
            for c in self.columns:
                q, t = c.to_query()
                columns.append((c.real_name(), t))
                select += f"{q},\n"
            select = select[:-2]
        else:
            select = "*"

        s += f"SELECT DISTINCT {select} FROM {self.tables[0]}"

        if len(self.joins) > 0:
            join = ""
            for e in self.joins:
                join += str(e)

            s += join

        if len(self.options) > 0:
            option = "\nWHERE "
            for e in self.options:
                o, a = e.to_query()
                option += o + "\nAND "
                args += a

            s += option[:-5]

        if len(self.group_by) > 0:
            s += "\nGROUP BY "
            for e in self.group_by:
                q = e.original_name()
                s += f"{q}, "
            s = s[:-2]

        if self.order_by != [] or self.order_by_random:
            s += "\nORDER BY "
            for e in self.order_by:
                q = e.real_name()
                s += f"{q},\n"

            s += "RANDOM(),\n"

            s = s[:-2]

        if self.limit > 0:
            s += f"\nLIMIT {self.limit}"

        return s, args, columns
