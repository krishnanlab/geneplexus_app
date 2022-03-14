

def test_index_page(client):
    response = client.get('http://127.0.0.1:5000/')
    print(response)
    return True