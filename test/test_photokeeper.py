import photokeeper.photokeeper as P
import pytest
import os
import logging

import smtplib
from mock import Mock
from mock import patch, call
from mock import MagicMock
from mock import PropertyMock


class Testphotokeeper:

    def setup(self):
        self.p = P.PhotoKeeper()
