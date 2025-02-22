from .generated import Root, RootImports, Err
from .generated.imports import Exit
from .generated.imports import Random
from .generated.imports import Stdin
from .generated.imports import Stdout
from .generated.imports import Stderr
from .generated.imports import streams
from .generated.imports import Preopens
from .generated.imports import Environment
from .generated.imports import Filesystem
from .generated.imports.filesystem import Descriptor, Filesize, ErrorCode, DescriptorType
from .generated import types as core_types
from typing import Mapping, Tuple, List

import sys
import os
from wasmtime import Store


class WasiRandom(Random):
    def get_random_bytes(self, len: int) -> bytes:
        return os.urandom(len)


class WasiStdin(Stdin):
    def get_stdin(self) -> streams.InputStream:
        return 0


class WasiStdout(Stdout):
    def get_stdout(self) -> streams.OutputStream:
        return 1


class WasiStderr(Stderr):
    def get_stderr(self) -> streams.OutputStream:
        return 2


class WasiPreopens(Preopens):
    def get_directories(self) -> List[Tuple[Descriptor, str]]:
        return []


class WasiStreams(streams.Streams):
    def drop_input_stream(self, this: streams.InputStream) -> None:
        return None

    def write(self, this: streams.OutputStream, buf: bytes) -> core_types.Result[int, streams.StreamError]:
        if this == 1:
            sys.stdout.buffer.write(buf)
        elif this == 2:
            sys.stderr.buffer.write(buf)
        else:
            raise NotImplementedError
        return core_types.Ok(len(buf))

    def blocking_write(self, this: streams.OutputStream, buf: bytes) -> core_types.Result[int, streams.StreamError]:
        return self.write(this, buf)

    def drop_output_stream(self, this: streams.OutputStream) -> None:
        return None


class WasiEnvironment(Environment):
    def get_environment(self) -> List[Tuple[str, str]]:
        return []


class WasiFilesystem(Filesystem):
    def write_via_stream(self, this: Descriptor, offset: Filesize) -> core_types.Result[streams.OutputStream, ErrorCode]:
        raise NotImplementedError

    def append_via_stream(self, this: Descriptor) -> core_types.Result[streams.OutputStream, ErrorCode]:
        raise NotImplementedError

    def get_type(self, this: Descriptor) -> core_types.Result[DescriptorType, ErrorCode]:
        raise NotImplementedError

    def drop_descriptor(self, this: Descriptor) -> None:
        raise NotImplementedError


class WasiExit(Exit):
    def exit(self, status: core_types.Result[None, None]) -> None:
        raise NotImplementedError


root = None
store = None


def init() -> Tuple[Root, Store]:
    global store
    global root
    if root is None:
        store = Store()
        root = Root(store, RootImports(WasiStreams(),
                                       WasiFilesystem(),
                                       WasiRandom(),
                                       WasiEnvironment(),
                                       WasiPreopens(),
                                       WasiExit(),
                                       WasiStdin(),
                                       WasiStdout(),
                                       WasiStderr()))
    return root, store


# Generates Python bindings for the given component.
#
# The `name` provided is used as the name of the `component` binary provided.
# The `component` argument is expected to be the binary representation of a
# component.
#
# This function returns a mapping of filename to contents of files that are
# generated to represent the Python bindings here.
def generate(name: str, component: bytes) -> Mapping[str, bytes]:
    root, store = init()
    result = root.generate(store, name, component)
    if isinstance(result, Err):
        raise RuntimeError(result.value)
    ret = {}
    for name, contents in result.value:
        ret[name] = contents
    return ret


__all__ = ['generate']
