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