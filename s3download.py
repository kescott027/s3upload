#!/usr/bin/python
# coding=utf-8
""" Module that copies files from a local directory
Checks for their existance in a preconfigured S3 bucket
if they do not exist in the S3 bucket, it copies each file
that does not exist to the new Python bucket.

Relies on an S3Bucket(object) which defines the endpoint S3bucket"""

import platform
import os
from os import listdir
from os.path import isfile, join
import boto3
import botocore
import admin


def listdirectory(path):
    """
    Lists the content of a directory

    rasies an error if the directory doesn't exist

    usage:

        listdirectory('directory path')

    returns - a list of object with file names as strings.
    """
    print("platform type is : {0}".format(platform.system()))

    print(path)

    if platform.system() == 'Windows':
        print (path)

    try:
        return [f for f in listdir(path) if isfile(join(path, f))]

    except OSError:
        return None


def list_s3files(mybucket, key, secret):
    """
    Returns a list of files from a given S3 bucket.

    Usage:

        list_s3files('bucketname', 'key', 'secret')

    returns - a list of objects with files names as strings.

    """
    bucket_list = []

    conn = S3Connection(key, secret)

    bucket = conn.get_bucket(mybucket)

    for key in bucket.list():
        bucket_list.append(key.name.encode('utf-8'))

    return bucket_list


def filelist_diff(desired_list, actual_list):
    """
    Returns a list of files that exist on your desired list,
    but not in your actual list.  called as follows:
    filelist_diff(desired_list, actual_list)
    """
    diff_list = []

    for item in desired_list:

        if item not in actual_list:
            diff_list.append(item)

    return diff_list


class S3Bucket(object):
    """
    Creates an S3Bucket object that we can use to associate
    buckets and file lists, and execute transfers.

    usage:

    S3Bucket(auth=authobject, bucket_name='my_bucket')
    """
    def __init__(self, auth=None, bucket_name=None):

        self.bucket_name = bucket_name
        self.s3object = None
        self.objectlist = None
        self.resource = boto3.resource('s3')

        if auth is not None:
            self.auth = auth
            self.resource = boto3.resource('s3',
                                           aws_access_key_id=self.auth.key,
                                           aws_secret_access_key=self.auth.secret)

    def exists(self):
        """
        S3Bucket.exists()

        checks to see if a specified bucket exists.

        If it exists, it returns True.
        If it does not exist, it returns an error.

        ex:
            mybucket = S3Bucket(auth=myauth, bucket='mybucket')
            if ! mybucket.exists():
                mybucket.init()
        """
        try:
            self.resource.meta.client.head_bucket(Bucket=self.bucket_name)

        except botocore.exceptions.ClientError as error:
            return int(error.response['Error']['Code'])

        try:
            self.s3object = self.resource.Bucket(self.bucket_name)
            self.get_objects()

        except botocore.exceptions.ClientError as error:
            return int(error.response['Error']['Code'])

        return True

    def init(self, bucket_name=None):
        """
        Checks for a bucket, if it doesn't exist, creates it.

        If the bucket name is None, raises ValueError
        """
        if bucket_name:
            setattr(self.bucket_name, bucket_name)

        elif self.bucket_name is None:
            raise ValueError

        if self.exists() is True:
            return True
        elif self.exists() == 404:
            try:
                self.resource.create_bucket(Bucket=self.bucket_name)
            except botocore.exceptions.ClientError as error:
                return error
        else:
            return self.exists()

        if self.auth is not None:
            self.resource = boto3.resource(
                's3',
                aws_access_key_id=self.auth.key,
                aws_secret_access_key=self.auth.secret)

        return True

    def get_objects(self):
        """
        Dumps and repopulates a list of objects in a given
        bucket.
        """
        if self.s3object is None:
            if self.exists is not True:
                raise ValueError

        try:
            self.objectlist = []

            for s3object in self.s3object.objects.all():
                # print(s3object.key)
                # input('\tpress any key for next item...')
                self.objectlist.append(s3object.key)

        except botocore.exceptions.ClientError as error:
            error_code = int(error.response['Error']['Code'])
            return error_code

        return True

    def add_object(self, new_object, retries=0):
        """
        Adds a file or files to the s3 bucket

        usage:

          S3Bucket.add_object('object name')
          alternatively:
          S3Bucket.add_object('list of object names')
        """
        if isinstance(new_object, list):
            return self.add_objects(new_object)

        try:
            new_object_data = open(new_object, mode='rb')

            try:
                self.s3object.put_object(Key=new_object, Body=new_object_data)
                self.get_objects()

            except botocore.exceptions.ClientError as error:

                if retries < 3:
                    retries += 1
                    self.add_object(new_object, retries)

                error_code = int(error.response['Error']['Code'])
                new_object_data.close()
                return error_code

        except IOError as error:

            if retries < 3:
                retries += 1
                self.add_object(new_object, retries)

            try:
                new_object_data.close()

            except NameError:
                pass

            return error

        new_object_data.close()
        return True

    def add_objects(self, object_list):
        """
        Adds a list of objects by name to the S3 bucket object destination.

        Future Improvements:
        return a dictionary with results in the format:
        {"object_name" : File_upload_result}
        """
        results = {}

        for file_object in object_list:

            try:
                self.add_object(file_object)
                results[file_object] = 'Successful'

            except botocore.exceptions.ClientError as error:
                error_code = int(error.response['Error']['Code'])
                return error_code

        self.get_objects()

        return results

    def multipart_transfer(self, file_object, s3_name, action):
        """
        Performs a multipart transfer of a given object.  useful for really
        really large objects.

        usage:
            S3Bucket.multipart_transfer('objectname')
        """

        if action == None:

            action = 'upload'
        else:

            pass


        if action == 'download':
            try:
                self.s3object.meta.client.download_file(self.bucket_name,
                                                        file_object,
                                                      s3_name)

            except botocore.exceptions.ClientError as error:
                error_code = int(error.response['Error']['Code'])
                return error_code

        if action == 'upload':
            try:
                self.s3object.meta.client.upload_file(file_object, self.bucket_name,
                                                      s3_name)

            except botocore.exceptions.ClientError as error:
                error_code = int(error.response['Error']['Code'])
                return error_code

        return True

    def delete_object(self, new_object):
        """
        Deletes an object from the S3 bucket.

        usage:
            S3Bucket.delete('objectname')
        returns True if Successful
        returns an error if failed.
        """
        try:
            self.s3object.delete_object(Bucket=self.bucket_name,
                                        Key=new_object)

        except botocore.exceptions.ClientError as error:
            error_code = int(error.response['Error']['Code'])
            return error_code

        return True


def main():
    """
    Main function executes the following:

    1.  Load configuration Data:
        a.  S3 Authentication information
        b.  Source/Destination paths
            i.  Source object filesystem path
            ii. Destination S3 Bucket

    2.  for each pair:
       a.  get a list of all source files
       b.  get a list of all destination filelist_diff
       c.  Check if all source files are replicated to Destination
           i.  if yes - report to datadog that all files are up to date.
           ii.  if no create an update list
       c.  upload all files that don't exist in the Destination
       d.  report to datadog that all files are up to date.
    """

    #  Generate Configuration Data
    auth = admin.KeySecret(source='.s32.secret')

    local_path = os.path.normcase(r"/Program Files/Microsoft SQL Server/MSSQL10_50.MSSQLSERVER/MSSQL/Backup/test/")
    mybucket = "mtkbackup"
    jobs = {local_path: mybucket}

    for key in jobs:
        bucket = S3Bucket(auth=auth, bucket_name=jobs[key])
        print(bucket.init())
        local_files = listdirectory(key)
        print("local files: {0}".format(local_files))
        # s3_files = list_s3files(jobs[key], auth.key,
        #                        auth.secret)
        print("remote files: {0}".format(bucket.objectlist))
        # input("type 0oS0bVxxXl||1sdfaksfoijs4fasi;jjdsfdalsjf;afejfwjfka;s to continue")
        to_upload_list = filelist_diff(bucket.objectlist, local_files)
        for item in to_upload_list:
            print(item)
            if item[0] != ".":
                dest_path = local_path + item
                print("parameters: {0}, {1}, {2}, {3}".format(bucket, item, os.path.normcase(dest_path), "download"))
                bucket.multipart_transfer(item, os.path.normcase(dest_path), "download")


if __name__ == "__main__":
    main()
