# Criar Banco de Dados
```bash
# VARIAVEIS, troque os valores se necessário
# postgres é o meu usuário
# mestrado é o nome do meu banco de dados
# 0000 e minha senha

# entrar com usuario postgres
psql -U postgres

# listar todas as datatable
\l

# encerrar conexao para dropar a tabela
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'mestrado';

# Deletar o bd anterior
DROP DATABASE mestrado;

# Criar o novo Banco de Dados
CREATE DATABASE mestrado
WITH ENCODING 'UTF8'
LC_COLLATE 'en_US.UTF-8'
LC_CTYPE 'en_US.UTF-8'
TEMPLATE template0;

# Dar permissão ao usuário
GRANT ALL PRIVILEGES ON DATABASE mestrado TO postgres;
ALTER DATABASE mestrado OWNER TO postgres;
```

# configurar database no mestrado/settings.py 
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'DB_name',  
        'USER': 'postgres',    
        'PASSWORD': '0000',  
        'HOST': 'localhost', 
        'PORT': '5432',   
    }
}
```

# Rodar as migrates
```bash
python manage.py migrate
```