import argparse

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

# parametros para correr el script en dataflow
# --runner DirectRunner / DataflowRunner
# --project <projectId>
# --job_name <job Name>
# --staging_location < Bucket where staging files will be>
# --temp_location < Bucket where temporal files will be>
# --db_host <database host>
# --db_user <user host>
# --db_password <Password Host>
# --db_name <database name>
# --bucket_to_list <bucket to list>
# --output <file where output will be>
# --requirements_file requirements.txt
# --template_location gs://[YOUR_BUCKET_NAME]/templates/mytemplate

"""
Parametros adicionales que sirven como parametros para la ejecucion
"""
class BucketToReadOptions(PipelineOptions):

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument('--bucket_to_list')
        parser.add_argument('--output')
        parser.add_argument('--db_host')
        parser.add_argument('--db_user')
        parser.add_argument('--db_password')
        parser.add_argument('--db_name')

"""
funcion de listado de archivos en el bucket
"""
def list_files(bucket):
    import googleapiclient.discovery

    service = googleapiclient.discovery.build('storage', 'v1')
    files = [file.get('name') for file in service.objects().list(
        bucket=bucket).execute().get("items", [])]

    return files

"""
Clase con la logica para obtener los tags de las fotos, logica de base de datos
"""
class GetData(beam.DoFn):

    def __init__(self, params):
        super(GetData, self).__init__()
        self.params = params
        self.conn = None
        self.gcs_client = None

    def _create_connection(self):
        import pg8000 as DBAPI
        import logging

        logging.info("conecting with db")
        self.conn = DBAPI.connect(
            host=self.params.db_host,
            user=self.params.db_user,
            password=self.params.db_password,
            database=self.params.db_name
        )

    def insert_test(self, key_, value_):
        import logging
        try:
            if self.conn is None:
                self._create_connection()

            sql = "insert into test(key_, value_) values(%s, %s)"
            cursor = self.conn.cursor()
            cursor.execute(sql, (key_, value_))
            self.conn.commit()
            cursor.close()
        except:
            logging.exception("error insert item")

    def _get_cloud_storage_bucket(self):
        from google.cloud import storage
        gcs_client = storage.Client()
        bucket_name = self.params.bucket_to_list
        return gcs_client.get_bucket(bucket_name)

    def get_tag(self, file_name):
        import StringIO
        from PIL import Image, ExifTags

        bucket = self._get_cloud_storage_bucket()
        blob = bucket.blob(file_name)
        string_buffer = StringIO.StringIO()
        blob.download_to_file(string_buffer)
        img = Image.open(string_buffer)
        tags = img._getexif()

        return {ExifTags.TAGS[k]: v for k, v in tags.items() if k in ExifTags.TAGS}
    """
    Proceso principal que se ejecuta en el pipeline
    """
    def process(self, file_name, *args, **kwargs):
        tags = self.get_tag(file_name)

        for k, v in tags.items():
            self.insert_test(k, v)

        return ["ok"]


"""
metodo principal de ejecucion y despliegue
"""
def run(argv):
    options = PipelineOptions(argv)
    bucket_to_read_options = options.view_as(BucketToReadOptions)
    pipeline = beam.Pipeline(options=options)

    pipeline | 'start bucket' >> beam.Create([bucket_to_read_options.bucket_to_list]) | \
        'list files from bucket' >> beam.ParDo(list_files) | \
        'add save tags in DB' >> beam.ParDo(GetData(bucket_to_read_options)) | \
        'save name files ' >> beam.io.WriteToText(bucket_to_read_options.output)

    pipeline.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    known, pipeline_args = parser.parse_known_args()

    run(pipeline_args)