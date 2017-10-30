## Python Dataflow Example

Este es un proyecto de demo en el cual se muestra como funciona dataflow

El objetivo de este pipeline es listar las imagenes que estan en un bucket en cloud storage y guardar en una base de 
datos postgresql.

## Ejecución local
1. Instalar python 2.7 y postgresql 9.4 o superior

1. Crear una base datos llamada test en el postgresql de la siguiente manera

    ```
        CREATE TABLE public.test
        (
            key_ character varying COLLATE pg_catalog."default",
            value_ character varying COLLATE pg_catalog."default"
        );
    ```
    
1. Clonar el proyecto con el siguiente comamndo

    ```
    git clone https://github.com/Eforcers/dataflow_images.git
    ```

1. Instalar las dependencias de dataflow

   ```
   cd dataflow_images
   pip install -r requirements_local.txt
   ```

1. Ejecutar con los siguientes parametros

     * --runner DirectRunner
     * --db_host [database host]
     * --db_user [user host]
     * --db_password [Password Host]
     * --db_name [database name]
     * --bucket_to_list <bucket to list
     * --output <file where output will be> 
     
   Un ejemplo de ejecución seria el siguiente

   ```
   python main.py  --runner DirectRunner --db_host 127.0.0.1 --db_user user_test --db_password qwerty1234 --db_name test_db  --bucket_to_list bucket_1 --output gs://bucket_2:/output.txt 
   ```

Despues de la ejecución verifique en la base de datos el resultado

## Despliegue
Para ejecutar el pipeline en Google dataflow hay que realizar los siguientes pasos 

1. Ejecutar los pasos de despliegue local hasta el paso 4

1. Ejecutar con los siguientes parametros
     * --runner DataflowRunner
     * --project <projectId>
     * --job_name <job Name>
     * --staging_location < Bucket where staging files will be>
     * --temp_location < Bucket where temporal files will be>
     * --db_host <database host>
     * --db_user <user host>
     * --db_password <Password Host>
     * --db_name <database name>
     * --bucket_to_list <bucket to list>
     * --output <file where output will be>
     * --requirements_file requirements.txt


   ```
   python main.py  --runner DataflowRunner --project projectId --job_name myjob01 --staging_location gs://bucket1/staging --temp_location gs://bucket1/temp --requirements_file requirements.txt --db_host db_host --db_user user_db --db_password user_password --db_name db_test --bucket_to_list bucket2 --output gs://bucket1/salida.txt
   ```
3. Despues de la ejecución verifique si esta ejecutando en Google Cloud Platform

## Subir como template
Para no tener que correr el script locamente para realizar la ejecución en la nube y tener una plantilla en 
dataflow hay que realizar los siguientes pasos
1. Para subir como template es necesario seguir los pasos de la ejecución local hasta el paso 4
1. Ejecutar con los siguientes parametros
     * --runner DataflowRunner
     * --staging_location < Bucket where staging files will be>
     * --requirements_file requirements.txt
     * --template_location gs://[YOUR_BUCKET_NAME]/templates/mytemplate
     
     ```
     python main.py  --runner DataflowRunner --staging_location gs://bucket1/staging --temp_location gs://bucket1/temp --requirements_file requirements.txt  --template_location gs://bucket1/templates/mytemplate
     ```