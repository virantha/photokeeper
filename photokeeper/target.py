# Copyright 2016 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc

class TargetBase(abc.ABC):

    @abc.abstractmethod
    def check_duplicates(self, images):
        """ Go through images and mark a property in each image if it's a duplicate in the target repository
            Each plugin target type can mark a different 'dup' property
        """

    @abc.abstractmethod
    def execute_copy(self, images):
        """ Take the source image files and copy/upload them to the target repository
        """
