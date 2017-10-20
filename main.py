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




def list_files(self, bucket):
    import googleapiclient.discovery

    service = googleapiclient.discovery.build('storage', 'v1')
    files = ["%s/%s" % (file.get('bucket'), file.get('name')) for file in service.objects().list(
        bucket=bucket.get()).execute().get("items", [])]

    return files

class GetData(beam.DoFn):
    def __init__(self, bucket_param):
        self.bucket = bucket_param.get()

    def process(self, file):
        from google.cloud import storage
        gcs_client = storage.Client()

        return ["pre_" + file]


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