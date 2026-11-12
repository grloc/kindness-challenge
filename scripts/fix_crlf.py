# Fix : convertir \n en \r\n et enlever le \n a la fin
with open('cleaned_resources.csv', 'rb') as f:
    data = f.read()

# On enlève tous les \r, on garde juste les lignes
text = data.decode().replace('\r\n', '\n').replace('\r', '\n')
lines = text.splitlines()

# On recolle avec \r\n, sans \r\n a la fin
fixed = '\r\n'.join(lines)

with open('cleaned_resources.csv', 'wb') as f:
    f.write(fixed.encode())

print('Fix fait ! Nouvelle taille :', len(fixed.encode()))