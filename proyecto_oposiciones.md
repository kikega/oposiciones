# Proyecto oposiciones

## Objetivo

El objetivo es preparar unas oposiciones para la administración pública, donde se han de estudiar unos temas y realizar unos test para evaluar el conocimiento adquirido.

La plicación será multiusuario y multioposición, de forma que cada usuario podrá tener sus propias oposiciones y sus propios temas. Los temas se pueden repetir para distintas oposiciones, porlo que se debe asignar los temas que se corresponden a una oposicion concreta

Los tests son preguntas de respuesta cerrada con 4 opciones (a, b, c y d), donde sólo una respuesta es la correcta. Cada oposición puede tener un número de preguntas por test diferente, por lo que se debe asignar el número de preguntas por test a cada oposición.

El usuario, puede estudiar temas por por separado, realizar test por untema concreto, o realizar test con preguntas de varios temas.

El usuario, puede realizar test de repaso, que son test con preguntas de temas ya estudiados, pero que se deben repasar para no olvidarlos y repasos de temas en los que se ha fallado más.

La aplicación debe llevar un control de los temas en los que mas se falla y sugerir repasos de esos temas, así como de repetir tests de preguntas que ya se han fallado.

Debe haber un control del tiempo que el usuario está activo en la aplicación y mostrar estadísticas de tiempo dedicado a cada tema.

Se debe controlar en un dashboard todos los datos referentes a la preparación de las oposiciones, como la nota media, el número de tests realizados, la nota máxima, el tiempo de estudio, el acierto global, etc.

El usuario podrá subir sus propios temas y preguntas para ampliar el contenido de estudio.

## Requisitos

- La base de datos que maneje la estructura de datos, será sqlite3 en desarrollo y postgresql en producción
- La aplicación será web y responsive, con un diseño moderno y atractivo
- La página principal, será un dashboard donde se muestren todas los datos y estadísticas necesarias, así como un menú para acceder a las diferentes funcionalidades de la aplicación
- Stack tecnológico
    - Python
    - Django
    - Bootstrap 5
    - Gráficos con chart.js
- Los requerimientos de librerias de la aplicación, está divididos en tres archivos, base.txt, desarrollo.txt y produccion.txt
- La configuración de la aplicación, está dividida en tres archivos, base.py, desarrollo.py y produccion.py, por lo que settings.py será una carpeta que contenga los tres archivos de configuración y un archivo __init__.py que importe el archivo de configuración correspondiente a la variable de entorno DJANGO_SETTINGS_MODULE
- La aplicación guarda logs de acceso y de consultas a la base de datos en 7 archivos rotatorios

## Estructura de datos

- Oposiciones, oposición a la que se presenta el usuario
- Bloques, que componen una oposición
- Temas, que componen un bloque
- Capitulos, que componen un tema
- Articulos, que componen un capitulo
- Preguntas, que componen un articulo
- Respuestas, que componen una pregunta
- Tests, tests que componen una oposición
- Estadisticas necesarias
- Usuarios, usuarios de la aplicación, donde utilizaran el correo electronico como nombre de usuario para hacer el login

## Seguridad

- La aplicacion debe tener una autenticacion de usuario y contraseña
- La aplicacion debe tener una sesion de usuario y contraseña
- El usuario se debe autenticar usando su correo electrónico, para lo que habrá que extender el modelo de usuario de django para que tenga un correo electronico y una contraseña.
- El usuario podrá cambiar su contraseña cuando lo desee
- Se deberar primar la seguridad de el sitio controlando en los formularios la entrada  de datos, para lo que se debera validar que los datos introducidos sean correctos y que no se introduzcan datos no validos.
- Se debera implementar un sistema de autenticacion que permita al usuario acceder a su cuenta y que le permita gestionar sus datos.
- Utiliza un archivo .env para guardar las variables de entorno, como por ejemplo la clave secreta de django, la configuracion de la base de datos, etc.