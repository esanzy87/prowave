"""
prowave.utils
"""
import glob
import os
import subprocess
import requests
from django.conf import settings


def download_pdb_form_rcsb(pdb_id):
    """
    RCSB로부터 4자리 PDB ID에 해당하는 PDB파일 다운로드
    pdb_sources_dir에 해당 PDB가 존재하면 단순 복사 존재하지 않으면 원격지 사이트로부터 다운로드하여 pdb_sources_dir에 저장

    :param pdb_id:
    :return: pdb content in binary
    """
    source_file_dir = os.path.join(settings.PDB_SOURCES_DIR, '%s' % pdb_id.upper()[:2])
    source_file_path = os.path.join(source_file_dir, '%s.pdb' % pdb_id.upper())
    if os.path.exists(source_file_path):
        with open(source_file_path, 'rb') as stream:
            return stream.read()
    try:
        response = requests.get("https://file.rcsb.org/download/%s.pdb" % pdb_id.lower())
        os.makedirs(os.path.dirname(source_file_path), exist_ok=True)
        with open(source_file_path, 'wb+') as stream:
            stream.write(response.content)
        return response.content
    except requests.exceptions.RequestException:
        raise AttributeError("Invalid PDB ID")


def get_rcsb_pdb(pdb_id, target_dir):
    """
    RCSB로부터 4자리 PDB ID에 해당하는 PDB파일 다운로드
    pdb_sources_dir에 해당 PDB가 존재하면 단순 복사 존재하지 않으면 원격지 사이트로부터 다운로드하여 pdb_sources_dir에 저장

    :param pdb_id:
    :param target_dir:
    :return: full_file_path
    """
    pdb_content = download_pdb_form_rcsb(pdb_id)
    full_file_path = os.path.join(target_dir, '%s.pdb' % pdb_id.upper())
    os.makedirs(target_dir, exist_ok=True)
    with open(full_file_path, 'wb') as stream:
        stream.write(pdb_content)
    return full_file_path


def save_uploaded_pdb(file, target_dir):
    """
    request.FILES 로부터 전달받은 file객체를 work dir에 저장

    :param file:
    :param target_dir:
    :return: full_file_path
    """
    os.makedirs(target_dir, exist_ok=True)
    full_file_path = os.path.join(target_dir, file.name)
    with open(full_file_path, 'wb+') as stream:
        for chunk in file.chunks():
            stream.write(chunk)
    return full_file_path


def files(target_dir):
    """
    list pdb files in directory
    """
    return [os.path.basename(f) for f in glob.glob(os.path.join(target_dir, '*.pdb'))]
