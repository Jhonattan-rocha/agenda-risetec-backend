import requests
print(len([1,2,3]))
dados_producto = {
  "name": "Cetim",
  "description": "tecido usado para moletons",
  "price": 100
}

print(dados_producto.popitem())

# req_prod = requests.post("http://127.0.0.1:8080/crud/products", json=dados_producto)

dados_categoria = {
  "name": "moletom"
}

# req_cat = requests.post("http://127.0.0.1:8080/crud/categories", json=dados_categoria)

dados_produto_categoria = {
  "id_prod": 1,
  "id_cat": 1
}

# req_prod_cat = requests.post("http://127.0.0.1:8080/crud/product_categories", json=dados_produto_categoria)

# print(req_prod_cat.text)

# req_prod_cat_del = requests.delete("http://127.0.0.1:8080/crud/product_categories/2")

# print(req_prod_cat_del)
