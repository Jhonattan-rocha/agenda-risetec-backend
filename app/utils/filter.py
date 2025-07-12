# app/utils/filter.py

from app.Mapping import models_mapping
from sqlalchemy.types import Integer, String, Float, Boolean, Date, DateTime
from sqlalchemy import and_, or_, func, Column
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased, contains_eager
from app.models.eventsModel import user_events_association
from app.models.userModel import User

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
            # Adicionado tratamento para 'Z' no final da string de data
            if isinstance(value, str) and value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        elif isinstance(column_type, String):
            return str(value)
        else:
            return value
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value '{value}' for column type {column_type}")


def apply_filters_dynamic(query, filters: str, model_name: str):
    db_model = models_mapping.get(model_name)
    if not db_model:
        return query

    # Dicionário para rastrear os joins já feitos e evitar duplicidade
    joined_models = {model_name: aliased(db_model, name="base_model")}

    # Divide os grupos de filtros (unidos por '$')
    filter_groups = filters.split('$')
    
    for group in filter_groups:
        group_conditions = []
        # Define o operador do grupo (AND por padrão, OR se houver '|')
        group_operator = or_ if '|' in group else and_
        rules = group.split('|') if '|' in group else group.split('$') # Suporta ambos como separador de regra
        
        # Correção para o caso de uma única regra no grupo
        if len(rules) == 1 and '$' not in rules[0] and '|' not in rules[0]:
            rules = [rules[0]]
        
        for rule_string in rules:
            parts = rule_string.split('+')
            if len(parts) != 3:
                continue

            field_path, operator, value = parts
            
            current_model_alias = joined_models[model_name]
            current_model_class = db_model
            
            # Navega pelos relacionamentos
            if '.' in field_path:
                relations = field_path.split('.')
                field_name = relations.pop() # O último é o campo
                
                # Itera sobre as relações para fazer os joins
                for i, relation_name in enumerate(relations):
                    # Se o relacionamento já foi "joinado", usa o alias existente
                    if relation_name in joined_models:
                        current_model_alias = joined_models[relation_name]
                        current_model_class = current_model_alias.entity
                        continue

                    # Lógica específica para o relacionamento 'users' em 'Events'
                    if model_name == 'Events' and relation_name == 'users':
                        user_alias = aliased(User)
                        query = query.join(user_events_association).join(user_alias)
                        joined_models['users'] = user_alias
                        current_model_alias = user_alias
                        current_model_class = User
                    else:
                        # Lógica de join genérica para outros relacionamentos
                        related_model_class = getattr(current_model_class, relation_name).property.mapper.class_
                        alias = aliased(related_model_class)
                        query = query.join(alias, getattr(current_model_class, relation_name))
                        joined_models[relation_name] = alias
                        current_model_alias = alias
                        current_model_class = related_model_class

                column = getattr(current_model_alias, field_name, None)
            else:
                # Campo direto no modelo base
                column = getattr(db_model, field_path, None)

            if column is None:
                continue
            
            try:
                converted_value = convert_to_column_type(column, value)
            except ValueError:
                continue

            # Constrói a condição SQLAlchemy com base no operador
            if operator == "eq":
                group_conditions.append(column == converted_value)
            elif operator == "ne":
                group_conditions.append(column != converted_value)
            elif operator == "lt":
                group_conditions.append(column < converted_value)
            elif operator == "le":
                group_conditions.append(column <= converted_value)
            elif operator == "gt":
                group_conditions.append(column > converted_value)
            elif operator == "ge":
                group_conditions.append(column >= converted_value)
            elif operator == "ct": # contains (case-insensitive)
                group_conditions.append(func.lower(column).like(f"%{str(converted_value).lower()}%"))
            elif operator == "sw": # starts with (case-insensitive)
                group_conditions.append(func.lower(column).like(f"{str(converted_value).lower()}%"))
            elif operator == "ew": # ends with (case-insensitive)
                group_conditions.append(func.lower(column).like(f"%{str(converted_value).lower()}"))
            elif operator == "in":
                values_list = [convert_to_column_type(column, v) for v in str(converted_value).split(',')]
                group_conditions.append(column.in_(values_list))

        if group_conditions:
            query = query.where(group_operator(*group_conditions))

    return query