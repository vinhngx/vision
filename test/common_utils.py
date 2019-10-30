import os
import shutil
import tempfile
import contextlib
import unittest
import argparse
import sys
import torch
import errno
import __main__


@contextlib.contextmanager
def get_tmp_dir(src=None, **kwargs):
    tmp_dir = tempfile.mkdtemp(**kwargs)
    if src is not None:
        os.rmdir(tmp_dir)
        shutil.copytree(src, tmp_dir)
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir)


ACCEPT = os.getenv('EXPECTTEST_ACCEPT')

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--accept', action='store_true')
args, remaining = parser.parse_known_args()
if not ACCEPT:
    ACCEPT = args.accept
for i, arg in enumerate(sys.argv):
    if arg == '--accept':
        del sys.argv[i]
        break


class MapNestedTensorObjectImpl(object):
    def __init__(self, tensor_map_fn):
        self.tensor_map_fn = tensor_map_fn

    def __call__(self, object):
        if isinstance(object, torch.Tensor):
            return self.tensor_map_fn(object)

        elif isinstance(object, dict):
            mapped_dict = {}
            for key, value in object.items():
                mapped_dict[self(key)] = self(value)
            return mapped_dict

        elif isinstance(object, (list, tuple)):
            mapped_iter = []
            for iter in object:
                mapped_iter.append(self(iter))
            return mapped_iter if not isinstance(object, tuple) else tuple(mapped_iter)

        else:
            return object


def map_nested_tensor_object(object, tensor_map_fn):
    impl = MapNestedTensorObjectImpl(tensor_map_fn)
    return impl(object)


# adapted from TestCase in torch/test/common_utils to accept non-string
# inputs and set maximum binary size
class TestCase(unittest.TestCase):
    def assertExpected(self, output, subname=None, rtol=None, atol=None):
        r"""
        Test that a python value matches the recorded contents of a file
        derived from the name of this test and subname.  The value must be
        pickable with `torch.save`. This file
        is placed in the 'expect' directory in the same directory
        as the test script. You can automatically update the recorded test
        output using --accept.

        If you call this multiple times in a single function, you must
        give a unique subname each time.
        """
        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text
        # NB: we take __file__ from the module that defined the test
        # class, so we place the expect directory where the test script
        # lives, NOT where test/common_utils.py lives.
        module_id = self.__class__.__module__
        munged_id = remove_prefix(self.id(), module_id + ".")
        test_file = os.path.realpath(sys.modules[module_id].__file__)
        expected_file = os.path.join(os.path.dirname(test_file),
                                     "expect",
                                     munged_id)

        subname_output = ""
        if subname:
            expected_file += "_" + subname
            subname_output = " ({})".format(subname)
        expected_file += "_expect.pkl"
        expected = None

        def accept_output(update_type):
            print("Accepting {} for {}{}:\n\n{}".format(update_type, munged_id, subname_output, output))
            torch.save(output, expected_file)
            MAX_PICKLE_SIZE = 50 * 1000  # 50 KB
            binary_size = os.path.getsize(expected_file)
            self.assertTrue(binary_size <= MAX_PICKLE_SIZE)

        try:
            expected = torch.load(expected_file)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            elif ACCEPT:
                return accept_output("output")
            else:
                raise RuntimeError(
                    ("I got this output for {}{}:\n\n{}\n\n"
                     "No expect file exists; to accept the current output, run:\n"
                     "python {} {} --accept").format(munged_id, subname_output, output, __main__.__file__, munged_id))

        if ACCEPT:
            equal = False
            try:
                equal = self.assertNestedTensorObjectsEqual(output, expected, rtol=rtol, atol=atol)
            except Exception:
                equal = False
            if not equal:
                return accept_output("updated output")
        else:
            self.assertNestedTensorObjectsEqual(output, expected, rtol=rtol, atol=atol)

    def assertNestedTensorObjectsEqual(self, a, b, rtol=None, atol=None):
        self.assertEqual(type(a), type(b))

        if isinstance(a, torch.Tensor):
            torch.testing.assert_allclose(a, b, rtol=rtol, atol=atol)

        elif isinstance(a, dict):
            self.assertEqual(len(a), len(b))
            for key, value in a.items():
                self.assertTrue(key in b, "key: " + str(key))

                self.assertNestedTensorObjectsEqual(value, b[key], rtol=rtol, atol=atol)
        elif isinstance(a, (list, tuple)):
            self.assertEqual(len(a), len(b))

            for val1, val2 in zip(a, b):
                self.assertNestedTensorObjectsEqual(val1, val2, rtol=rtol, atol=atol)

        else:
            self.assertEqual(a, b)
