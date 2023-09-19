# Copyright 2022 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Internal shared classes for ForEach."""

from typing import Any, Sequence, Callable, Optional, Dict, Union

import attr
from tfx.dsl.context_managers import dsl_context
from tfx.types import channel as channel_types
from tfx.utils import typing_utils

# Avoid cyclic dependency
_BaseNode = Any


@attr.s(auto_attribs=True, kw_only=True, hash=False, eq=False)
class ForEachContext(dsl_context.DslContext):
  """DslContext for ForEach."""
  wrapped_channel: Optional[channel_types.BaseChannel] = None

  def __hash__(self) -> int:
    return hash(id(self))

  def __eq__(self, other: Any) -> bool:
    return other is self

  def validate(self, containing_nodes: Sequence[_BaseNode]):
    for parent in self.ancestors:
      if isinstance(parent, ForEachContext):
        raise NotImplementedError('Nested ForEach block is not supported yet.')

    if len(containing_nodes) > 1:
      raise NotImplementedError(
          'Cannot define more than one component within ForEach yet.')

    # TODO(b/237363715): Raise if contaning nodes does not use loop variable
    # neither directly nor indirectly.


_ChannelDict = Dict[str, channel_types.BaseChannel]
LoopVar = Union[channel_types.BaseChannel, _ChannelDict]


class Loopable:
  """A loopable object can be used with ForEach.

  with ForEach(loopable) as handle:
    ...

  A `handle` object would be generated by calling the `loop_var_factory` with
  the corresponding `ForEachContext`. Return value of the `loop_var_factory`
  would be passed as an `handle`.
  """

  def __init__(
      self, loop_var_factory: Callable[[ForEachContext], LoopVar]):
    if not callable(loop_var_factory):
      raise ValueError(f'{loop_var_factory} is not callable.')
    self._loop_var_factory = loop_var_factory

  def get_loop_var(self, context: ForEachContext) -> LoopVar:
    result = self._loop_var_factory(context)
    if not typing_utils.is_compatible(result, LoopVar):
      raise ValueError(f'ForEach got non-loopable instance {result}')
    return result

  def __getitem__(self, *unused_args):
    raise RuntimeError(
        'Cannot use loopable value directly. Please use ForEach to wrap it.')