import clamd
from six import BytesIO
from contextlib import contextmanager
import tempfile
import shutil
import os
import stat

from nose.tools import ok_, eq_, assert_true

mine = (stat.S_IREAD | stat.S_IWRITE)
other = stat.S_IROTH
execute = (stat.S_IEXEC | stat.S_IXOTH)


@contextmanager
def mkdtemp(*args, **kwargs):
    temp_dir = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


class TestUnixSocket():
    def setup(self):
        self.cd = clamd.ClamdUnixSocket()

    def test_ping(self):
        assert_true(self.cd.ping())

    def test_version(self):
        ok_(self.cd.version().startswith("ClamAV"))

    def test_reload(self):
        eq_(self.cd.reload(), 'RELOADING')

    def test_scan(self):
        with tempfile.NamedTemporaryFile(prefix="python-clamd") as f:
            f.write(clamd.EICAR)
            f.flush()
            os.fchmod(f.fileno(), (mine | other))
            eq_(self.cd.scan(f.name),
                {f.name: ('FOUND', 'Eicar-Test-Signature')}
            )

    def test_multiscan(self):
        expected = {}
        with mkdtemp(prefix="python-clamd") as d:
            for i in range(10):
                with open(os.path.join(d, "file" + str(i)), 'w') as f:
                    f.write(clamd.EICAR)
                    os.fchmod(f.fileno(), (mine | other))
                    expected[f.name] = ('FOUND', 'Eicar-Test-Signature')
            os.chmod(d, (mine | other | execute))

            eq_(self.cd.multiscan(d), expected)

    def test_instream(self):
        eq_(
            self.cd.instream(BytesIO(clamd.EICAR)),
            {'stream': ('FOUND', 'Eicar-Test-Signature')}
        )