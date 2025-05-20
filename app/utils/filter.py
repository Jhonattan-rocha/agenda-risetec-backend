from app.Mapping import models_mapping
from sqlalchemy.types import Integer, String, Float, Boolean, Date, DateTime
from sqlalchemy import and_, or_, func, Column
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased

def convert_to_column_type(column, value):
    column_type = column.type

    try:
        if isinstance(column_type, Integer):
            return int(value)
        elif isinstance(column_type, Float):
            return float(value)
        elif isinstance(column_type, Boolean):
            return value.lower() in ['true', '1', 'yes']
        elif isinstance(column_type, Date) or isinstance(column_type, DateTime):
            return datetime.fromisoformat(value)
        elif isinstance(column_type, String):
            return str(value)
        else:
            return value  # Fallback: tenta usar o valor como está
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value '{value}' for column type {column_type}")


def apply_filters_dynamic(query, filters: str, model):
    conditions = []
    db_model = models_mapping[model] if model in models_mapping.keys() else models_mapping["*"]
    joined_models = {}
    condition_rule = "and"
    filter_parts = []

    if "$" in filters:
        filter_parts = filters.split("$")
    else:
        filter_parts = filters.split("|")
        condition_rule = "or"

    for filter_string in filter_parts:
        aux = filter_string.split("+")

        if len(aux) == 3:
            field, operator, value = aux
            column: Column = getattr(db_model, field)

            # Verifica se é um campo relacionado
            if "." in field:
                relation_name, related_field = field.split(".")
                
                # Recupera o modelo relacionado
                related_model = getattr(db_model, relation_name, None)
                if not related_model:
                    continue  # Ignorar se a relação não existe
                
                if relation_name not in joined_models:
                    alias = aliased(models_mapping[relation_name])
                    query = query.join(alias, getattr(db_model, relation_name))
                    joined_models[relation_name] = alias
                
                column = getattr(joined_models[relation_name], related_field, None)
                if not column:
                    continue  # Ignorar se o campo relacionado não existe
            else:
                column = getattr(db_model, field, None)
                if not column:
                    continue  # Ignorar se o campo não existe
            
            try:
                value = convert_to_column_type(column, value)
            except ValueError as e:
                continue

            if operator == "eq":  # equals
                conditions.append(column == value)
            elif operator == "ne":  # not equals
                conditions.append(column != value)
            elif operator == "lt":  # less than
                conditions.append(column < value)
            elif operator == "le":  # less than or equal to
                conditions.append(column <= value)
            elif operator == "gt":  # greater than
                conditions.append(column > value)
            elif operator == "ge":  # greater than or equal to
                conditions.append(column >= value)
            elif operator == "ct":  # contains
                conditions.append(func.lower(column).like(f"%{value}%".lower()))
            elif operator == "sw":  # starts with
                conditions.append(func.lower(column).like(f"{value}%".lower()))
            elif operator == "ew":  # ends with
                conditions.append(func.lower(column).like(f"%{value}".lower()))
            elif operator == "sew":
                aux = value.split("_")
                if len(aux) == 2:
                    conditions.append(func.lower(column).like(f"{aux[0]}%{aux[1]}".lower()))
            elif operator == "in":
                conditions.append(column.in_([convert_to_column_type(column, val) for val in str(value).split(',')]))
            elif operator == "between":
                min_val, max_val = map(lambda x: convert_to_column_type(column, x), value.split(","))
                conditions.append(column.between(min_val, max_val))
            elif operator == "week_eq":
                week_number, year = map(int, value.split(","))
                conditions.append(func.week(column) == week_number)
                conditions.append(func.year(column) == year)
            elif operator == "avg_gt":
                conditions.append(func.avg(column) > value)
            elif operator == "sum_eq":
                conditions.append(func.sum(column) == value)
            elif operator == "count_lt":
                conditions.append(func.count(column) < value)
                
        if len(aux) == 2:
            constraint, column = aux

            if constraint == 'order_by':
                query = query.order_by(column if column else None)
            elif constraint == "last_days":
                days_ago = datetime.now() - timedelta(days=int(value))
                conditions.append(column >= days_ago)
            elif constraint == "next_days":
                days_ahead = datetime.now() + timedelta(days=int(value))
                conditions.append(column <= days_ahead)
                
    if conditions and condition_rule == "and":
        query = query.where(and_(*conditions))
    else:
        query = query.where(or_(*conditions))

    return query
