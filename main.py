import sys
import os
import argparse

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'lib'))

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

# parametros para correr el script en dataflow
# --runner DataflowRunner/DirectRunner \  #runner con el que se va a correr puede ser en gcp o local
# --project cprietorodriguez \ #proyecto en el que se corre
# --job_name myjob18 \ # nombre del job
# --staging_location gs://cp001/staging \ # bucket donde se ponen las librerias
# --temp_location gs://cp001/temp # carpeta para temporales


class BucketToReadOptions(PipelineOptions):

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument(
            '--bucket_to_list',
            default='cp001-r1',
            help='bucket name to list objects')
        parser.add_argument(
            '--output',
            default='gs://cp001/salida.txt',
            help='Output file to write results to.')
        parser.add_argument('db_host')
        parser.add_argument('db_user')
        parser.add_argument('db_password')
        parser.add_argument('db')


def list_files(bucket):
    import googleapiclient.discovery

    service = googleapiclient.discovery.build('storage', 'v1')
    files = [file.get('name') for file in service.objects().list(
        bucket=bucket.get()).execute().get("items", [])]

    return files


class GetData(beam.DoFn):

    def __init__(self, bucket_param):
        super(GetData, self).__init__()
        self.bucket_param = bucket_param
        self.conn = None
        self.gcs_client = None

    def _create_connection(self):
        import pg8000 as DBAPI
        import logging

        logging.info("conecting with db")
        self.conn = DBAPI.connect(host="35.196.223.204", user="eforcers", password="Ove52SWE", database="test")

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
        bucket_name = self.bucket_param.get()
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

        return {ExifTags.TAGS[k]: v for k, v in tags.items if k in ExifTags.TAGS}

    def process(self, file_name, *args, **kwargs):
        tags = self.get_tag(file_name)

        for k, v in tags.items():
            self.insert_test(k, v)

        return ["ok"]


def run(argv):
    options = PipelineOptions(argv)
    bucket_to_read_options = options.view_as(BucketToReadOptions)
    pipeline = beam.Pipeline(options=options)

    pipeline | 'start bucket' >> beam.Create([bucket_to_read_options.bucket_to_list]) | \
        'list files from bucket' >> beam.ParDo(list_files) | \
        'add save tags in DB' >> beam.ParDo(GetData(bucket_to_read_options.bucket_to_list)) | \
        'save name files ' >> beam.io.WriteToText(bucket_to_read_options.output)

    pipeline.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    known, pipeline_args = parser.parse_known_args()

    run(pipeline_args)