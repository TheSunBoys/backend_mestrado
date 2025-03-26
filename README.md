config database in mestrado/settings.py 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'DB_name',  
        'USER': 'postgres',    
        'PASSWORD': '',  
        'HOST': 'localhost', 
        'PORT': '5432',   
    }
}
entrar com usuario postgres
psql -U postgres
listar todas as datatable
\l

encerrar conexao para dropar a tabela
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'meubanco';

DROPAR

DROP DATABASE meubanco;

RECRIAR

CREATE DATABASE meubanco
WITH ENCODING 'UTF8'
LC_COLLATE 'en_US.UTF-8'
LC_CTYPE 'en_US.UTF-8'
TEMPLATE template0;
DAR PERMISSAO AO USUARIO
GRANT ALL PRIVILEGES ON DATABASE meubanco TO meuusuario;
ALTER DATABASE meubanco OWNER TO meuusuario;

python manage.py migrate