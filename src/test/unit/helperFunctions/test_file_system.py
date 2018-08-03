from common_helper_files import get_files_in_dir
import os
import unittest
import pytest
from tempfile import TemporaryDirectory
from pathlib import Path

from helperFunctions.fileSystem import get_parent_dir, get_src_dir, \
    get_test_data_dir, get_absolute_path, get_file_type_from_path, file_is_empty, \
    get_chroot_path, get_chroot_path_excluding_extracted_dir, get_faf_bin_dir, get_template_dir,\
    create_dir_for_file, compress_and_pack_folder


class TestFileSystemHelpers(unittest.TestCase):

    def setUp(self):
        self.current_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.current_cwd)

    def test_get_parent_dir(self):
        self.assertEqual(get_parent_dir('/foo/bar/test'), '/foo/bar', 'parent directory')

    def check_correct_src_dir(self, working_directory):
        real_src_dir = get_src_dir()
        os.chdir(working_directory)
        self.assertTrue(os.path.exists('{}/helperFunctions/fileSystem.py'.format(real_src_dir)), 'fileSystem.py found in correct place')
        self.assertEqual(get_src_dir(), real_src_dir, 'same source dir before and after chdir')

    def test_get_src_dir_cwd(self):
        self.check_correct_src_dir(os.getcwd())

    def test_get_src_dir_root(self):
        self.check_correct_src_dir('/')

    def test_get_template_dir(self):
        template_dir = get_template_dir()
        self.assertTrue(os.path.isdir(template_dir), 'template dir not found')
        file_suffixes_in_template_dir = [os.path.basename(f).split('.')[-1] for f in os.listdir(template_dir)]
        self.assertTrue('html' in file_suffixes_in_template_dir)

    def test_get_faf_bin_dir(self):
        bin_dir = get_faf_bin_dir()
        files_in_bin_dir = [os.path.basename(f) for f in get_files_in_dir(bin_dir)]
        self.assertTrue(os.path.isdir(bin_dir))
        self.assertIn('src/bin', bin_dir)
        self.assertIn('custommime.mgc', files_in_bin_dir)

    def test_get_absolute_path(self):
        abs_path = '/foo/bar'
        self.assertEqual(get_absolute_path(abs_path), '/foo/bar', 'absolute path of absolute path not correct')
        rel_path = 'foo/bar'
        self.assertEqual(get_absolute_path(rel_path, base_dir='/the'), '/the/foo/bar', 'absolute path of relative path not correct')

    def test_get_chroot_path(self):
        a = get_chroot_path('/foo/bar/com', '/foo/')
        self.assertEqual(a, '/bar/com', 'simple case with /')
        b = get_chroot_path('/foo/bar/com', '/foo')
        self.assertEqual(b, '/bar/com', 'simple case without /')
        c = get_chroot_path('/foo/bar/com', '/bar')
        self.assertEqual(c, '/foo/bar/com', 'none matching root')

    def test_get_chroot_excluding_extracted_prefix_dir(self):
        d = get_chroot_path_excluding_extracted_dir('/foo/faf_extracted/bar/com', '/foo')
        self.assertEqual(d, '/bar/com', 'including extracted')

    def test_get_file_type_system_magic(self):
        file_type = get_file_type_from_path('{}/container/test.zip'.format(get_test_data_dir()))
        self.assertEqual(file_type['mime'], 'application/zip', 'mime type not correct')
        self.assertEqual(file_type['full'], 'Zip archive data, at least v2.0 to extract', 'full type not correct')

    def test_get_file_type_custom_magic(self):
        file_type = get_file_type_from_path('{}/helperFunctions/ros_header'.format(get_test_data_dir()))
        self.assertEqual(file_type['mime'], 'firmware/ros', 'mime type not correct')
        self.assertEqual(file_type['full'], 'ROS Container', 'full type not correct')

    def test_file_is_zero(self):
        self.assertTrue(file_is_empty('{}/zero_byte'.format(get_test_data_dir())), 'file is empty but stated differently')
        self.assertFalse(file_is_empty('{}/get_files_test/testfile1'.format(get_test_data_dir())), 'file not empty but stated differently')
        self.assertFalse(file_is_empty(os.path.join(get_test_data_dir(), 'broken_link')), 'Broken link is not empty')

    def test_file_is_zero_broken_link(self):
        self.assertFalse(file_is_empty(os.path.join(get_test_data_dir(), 'broken_link')), 'Broken link is not empty')

    def test_get_file_type_of_internal_link_representation(self):
        file_type = get_file_type_from_path(os.path.join(get_test_data_dir(), 'symbolic_link_representation'))
        self.assertEqual(file_type['full'], 'symbolic link to \'/tmp\'')
        self.assertEqual(file_type['mime'], 'inode/symlink')


@pytest.mark.parametrize('out_file, out_folder', [
    ('test.txt', ''),
    ('folder/test.txt', 'folder'),
    ('folder/sub_folder/test.txt', 'folder/sub_folder')
])
def test_create_dir_for_file(out_file, out_folder):
    tmp_dir = TemporaryDirectory(prefix='FACT_test_')
    root_path = tmp_dir.name
    test_file_path = Path(root_path, out_file)
    create_dir_for_file(test_file_path)
    folder_path = Path(root_path, out_folder)
    assert folder_path.exists()
    assert folder_path.is_dir()
    tmp_dir.cleanup()


def test_compress_and_pack_folder():
    tmp_dir = TemporaryDirectory(prefix='FACT_test_')
    root_path = tmp_dir.name
    input_path = Path(get_test_data_dir(), 'get_files_test')
    file_path = Path(root_path, 'test.tar.gz')
    output_file_path = compress_and_pack_folder(input_path, file_path)
    assert file_path == output_file_path
    assert output_file_path.exists()
    tmp_dir.cleanup()


def test_compress_and_pack_folder_error():
    tmp_dir = TemporaryDirectory(prefix='FACT_test_')
    root_path = tmp_dir.name
    input_path = Path('/none/existing/path')
    file_path = Path(root_path, '')
    output_file_path = compress_and_pack_folder(input_path, file_path)
    assert output_file_path is None
    tmp_dir.cleanup()
