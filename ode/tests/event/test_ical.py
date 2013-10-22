# -*- encoding: utf-8 -*-
from unittest import TestCase
from datetime import datetime

import icalendar

from ode.models import DBSession, Event
from ode.tests.event import TestEventMixin


class TestGetEvent(TestEventMixin, TestCase):

    def get_event(self, **kwargs):
        event = self.create_event(**kwargs)
        DBSession.flush()

        response = self.app.get('/events/%s' % event.id,
                                headers={'Accept': 'text/calendar'})
        return event, response

    def test_content_type(self):
        event, response = self.get_event()
        self.assertEqual(response.content_type, 'text/calendar')

    def test_summary(self):
        event, response = self.get_event(title='A Title')
        self.assertContains(response, u'SUMMARY:%s' % event.title)

    def test_description(self):
        event, response = self.get_event(description='A description')
        self.assertContains(response,
                            u'DESCRIPTION:%s' % event.description.strip()[:10])

    def test_location(self):
        event, response = self.get_event(location_name='Location Name')
        self.assertContains(response,
                            u'LOCATION:%s' % event.location_name)

    def test_url(self):
        event, response = self.get_event(url='http://example.com/')
        self.assertContains(response, u'URL:%s' % event.url)

    def test_start_time(self):
        _, response = self.get_event(start_time=datetime(2013, 12, 25, 15, 0))
        self.assertContains(response, u'DTSTART;VALUE=DATE-TIME:20131225T1500')

    def test_end_time(self):
        _, response = self.get_event(end_time=datetime(2013, 12, 25, 15, 0))
        self.assertContains(response, u'DTEND;VALUE=DATE-TIME:20131225T1500')


class TestGetEventList(TestEventMixin, TestCase):

    def test_list_events(self):
        self.create_event(title=u'Événement 1')
        self.create_event(title=u'Événement 2')
        response = self.app.get('/events',
                                headers={'Accept': 'text/calendar'})
        self.assertContains(response, u'SUMMARY:Événement 1')
        self.assertContains(response, u'SUMMARY:Événement 2')


class TestPostEvent(TestEventMixin, TestCase):

    start_time = datetime(2013, 12, 25, 15, 0)

    def make_icalendar(self, titles):
        calendar = icalendar.Calendar()
        for title in titles:
            event = icalendar.Event()
            event.add('summary', title)
            event.add('dtstart', self.start_time)
            calendar.add_component(event)
        return calendar.to_ical()

    def test_post_single_event(self):
        calendar = self.make_icalendar(titles=[u'Événement'])
        response = self.app.post('/events', calendar,
                                 headers={'content-type': 'text/calendar'})
        self.assertEqual(response.json['status'], 'created')
        event = DBSession.query(Event).filter_by(title=u'Événement').one()
        self.assertEqual(event.start_time, self.start_time)