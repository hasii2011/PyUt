
from logging import Logger
from logging import getLogger

from unittest import TestSuite
from unittest import main as unitTestMain

from org.pyut.general.SemanticVersion import SemanticVersion
from org.pyut.preferences.PyutPreferences import PyutPreferences

from tests.TestBase import TestBase

from org.pyut.general.GithubAdapter import GithubAdapter


class TestGithubAdapter(TestBase):
    """
    """
    clsLogger: Logger = None

    @classmethod
    def setUpClass(cls):
        TestBase.setUpLogging()
        TestGithubAdapter.clsLogger = getLogger(__name__)
        PyutPreferences.determinePreferencesLocation()

    def setUp(self):
        self.logger:        Logger        = TestGithubAdapter.clsLogger
        self.githubAdapter: GithubAdapter = GithubAdapter()

    def tearDown(self):
        self.githubAdapter.cleanUp()
        del self.githubAdapter

    def testGetLatestVersionNumber(self):
        try:
            latestReleaseNumber: SemanticVersion = self.githubAdapter.getLatestVersionNumber()
            self.logger.info(f'Pyut latest release number: {latestReleaseNumber}')
        except (ValueError, Exception) as e:
            self.logger.error(f'{e}')


def suite() -> TestSuite:
    """You need to change the name of the test class here also."""
    import unittest

    testSuite: TestSuite = TestSuite()
    # noinspection PyUnresolvedReferences
    testSuite.addTest(unittest.makeSuite(TestGithubAdapter))

    return testSuite


if __name__ == '__main__':
    unitTestMain()
