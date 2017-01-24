"""Acceptance tests for LMS-hosted Programs pages"""
from nose.plugins.attrib import attr

from common.test.acceptance.fixtures.catalog import CatalogFixture, CatalogConfigMixin
from common.test.acceptance.fixtures.programs import ProgramsConfigMixin
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.programs import ProgramListingPage, ProgramDetailsPage
from openedx.core.djangoapps.catalog.tests.factories import (
    ProgramFactory, CourseFactory, CourseRunFactory
)


class ProgramPageBase(ProgramsConfigMixin, CatalogConfigMixin, UniqueCourseTest):
    """Base class used for program listing page tests."""
    def setUp(self):
        super(ProgramPageBase, self).setUp()

        self.set_programs_api_configuration(is_enabled=True)

        self.programs = ProgramFactory.create_batch(3)
        self.stub_catalog_api()

    def create_program(self):
        """DRY helper for creating test program data."""
        course_run = CourseRunFactory(key=self.course_id)
        course = CourseFactory(course_runs=[course_run])

        return ProgramFactory(courses=[course])

    def stub_catalog_api(self, data=None):
        """Stub out the catalog API's program and course run endpoints."""
        self.set_catalog_configuration(is_enabled=True)
        CatalogFixture().install_programs(data or self.programs)

    def auth(self, enroll=True):
        """Authenticate, enrolling the user in the configured course if requested."""
        CourseFixture(**self.course_info).install()

        course_id = self.course_id if enroll else None
        AutoAuthPage(self.browser, course_id=course_id).visit()


class ProgramListingPageTest(ProgramPageBase):
    """Verify user-facing behavior of the program listing page."""
    def setUp(self):
        super(ProgramListingPageTest, self).setUp()

        self.listing_page = ProgramListingPage(self.browser)

    def test_no_enrollments(self):
        """Verify that no cards appear when the user has no enrollments."""
        self.stub_catalog_api()
        self.auth(enroll=False)

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_no_programs(self):
        """
        Verify that no cards appear when the user has enrollments
        but none are included in an active program.
        """
        self.stub_catalog_api()
        self.auth()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_enrollments_and_programs(self):
        """
        Verify that cards appear when the user has enrollments
        which are included in at least one active program.
        """
        program = self.create_program()
        self.stub_catalog_api(data=[program])
        self.auth()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)


@attr('a11y')
class ProgramListingPageA11yTest(ProgramPageBase):
    """Test program listing page accessibility."""
    def setUp(self):
        super(ProgramListingPageA11yTest, self).setUp()

        self.listing_page = ProgramListingPage(self.browser)

        program = self.create_program()
        self.stub_catalog_api(data=[program])

    def test_empty_a11y(self):
        """Test a11y of the page's empty state."""
        self.auth(enroll=False)
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_cards_a11y(self):
        """Test a11y when program cards are present."""
        self.auth()
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()


@attr('a11y')
class ProgramDetailsPageA11yTest(ProgramPageBase):
    """Test program details page accessibility."""
    def setUp(self):
        super(ProgramDetailsPageA11yTest, self).setUp()

        self.details_page = ProgramDetailsPage(self.browser)

        program = self.create_program()
        program['uuid'] = self.details_page.program_uuid

        self.stub_catalog_api(data=program)

    def test_a11y(self):
        """Test the page's a11y compliance."""
        self.auth()
        self.details_page.visit()
        self.details_page.a11y_audit.check_for_accessibility_errors()
