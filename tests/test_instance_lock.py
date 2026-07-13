import os
import unittest

from execution.instance_lock import acquire, release, _pid_alive


class TestInstanceLock(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_bot.lock')
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))

    def test_acquire_fresh(self):
        ok, holder = acquire(self.path)
        self.assertTrue(ok)
        self.assertEqual(holder, os.getpid())
        self.assertTrue(os.path.exists(self.path))

    def test_blocked_by_live_other_pid(self):
        # PID 1 always exists; simulate another live instance holding the lock.
        with open(self.path, 'w') as fh:
            fh.write('1')
        ok, holder = acquire(self.path)
        self.assertFalse(ok)
        self.assertEqual(holder, 1)

    def test_reclaims_stale_lock(self):
        # A very high PID that isn't running -> stale -> reclaimed.
        with open(self.path, 'w') as fh:
            fh.write('2147480000')
        ok, holder = acquire(self.path)
        self.assertTrue(ok)
        self.assertEqual(holder, os.getpid())

    def test_release_removes_owned_lock(self):
        acquire(self.path)
        release(self.path)
        self.assertFalse(os.path.exists(self.path))

    def test_release_leaves_other_lock(self):
        with open(self.path, 'w') as fh:
            fh.write('1')  # not ours
        release(self.path)
        self.assertTrue(os.path.exists(self.path))

    def test_pid_alive_self(self):
        self.assertTrue(_pid_alive(os.getpid()))

    def test_pid_alive_bogus(self):
        self.assertFalse(_pid_alive(-1))


if __name__ == '__main__':
    unittest.main()
