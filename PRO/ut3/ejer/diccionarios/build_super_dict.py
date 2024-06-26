# ***************************
# DICCIONARIO EN CONSTRUCCIÓN
# ***************************


def run(items: list) -> dict:
    unpack_items = {}
    titles = []
    for item in range(len(items)):
        titles.append(items[item][0])
        del items[item][0]

    for title in range(len(titles)):
        unpack_items[titles[title]] = items[title]


    

    return unpack_items


if __name__ == '__main__':
    run([['Episode IV - A New Hope', 'May 25', 1977, 'George Lucas'], ['Episode V - The Empire Strikes Back', 'May 21', 1980], ['Episode VI - Return of the Jedi', 'May 25', 1983]])