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

    def process(self, file_name, *args, **kwargs):
        from google.cloud import storage
        import StringIO
        from PIL import Image, ExifTags
        import psycopg2
        import logging

        gcs_client = storage.Client()
        bucket_name = self.bucket_param.get()
        bucket = gcs_client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)

        string_buffer = StringIO.StringIO()
        blob.download_to_file(string_buffer)
        img = Image.open(string_buffer)

        tags = img._getexif()

        conn_string = "host='35.196.223.204' dbname='test' " \
                      "user='eforcers' password='Ove52SWE'"

        logging.info("Connecting to database\n	->%s", conn_string)

        try:
            conn = psycopg2.connect(conn_string)
        except Exception as ex:
            logging.exception("error connecting with db")

        cursor = conn.cursor()
        sql = "insert into test(key_, value_) values(%s, %s)"
        ex = {}
        for k, v in tags.items():
            if k in ExifTags.TAGS:
                try:
                    cursor.execute(sql, (ExifTags.TAGS[k], v))
                    conn.commit()
                    ex[ExifTags.TAGS[k]] = v
                except Exception as e:
                    logging.exception("error sending info to db ")
        cursor.close()

        return [ex]


def run(argv):
    options = PipelineOptions(argv)
    bucket_to_read_options = options.view_as(BucketToReadOptions)
    pipeline = beam.Pipeline(options=options)

    pipeline | 'start bucket' >> beam.Create([bucket_to_read_options.bucket_to_list]) | \
        'list files from bucket' >> beam.ParDo(list_files) | \
        'add prefix' >> beam.ParDo(GetData(bucket_to_read_options.bucket_to_list)) | \
        'save name files ' >> beam.io.WriteToText(bucket_to_read_options.output)

    pipeline.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    known, pipeline_args = parser.parse_known_args()

    run(pipeline_args)