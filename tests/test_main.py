import pytest

import findspark
findspark.init()

from pyspark import SparkConf, SparkContext
from background_hang_reporter_job import *

# allows us to check deep equality while accounting for floating point error
def assert_deep_equality(actual, expected):
    t = type(actual)
    te = type(expected)

    if t is dict and te is dict:
        assert len(actual) == len(expected)
        for k, v in actual.iteritems():
            assert k in expected
            assert_deep_equality(v, expected[k])
    elif (t is list or t is tuple) and (t == te):
        assert len(actual) == len(expected)
        for a,e in zip(actual, expected):
            assert_deep_equality(a, e)
    elif te is float:
        epsilon = 0.000001
        assert abs(actual - expected) < epsilon
    else:
        assert actual == expected

# Initialize a spark context:
@pytest.fixture(scope="session")
def spark_context(request):
    conf = SparkConf().setMaster("local")\
        .setAppName("background_hang_reporter_job" + "_test")
    sc = SparkContext(conf=conf)

    # teardown
    request.addfinalizer(lambda: sc.stop())

    return sc

def create_parent_ping(os, build_id, subsession_length, thread_hang_stats):
    hang_stats = []
    for stat in thread_hang_stats:
        thread_name, stacks, histograms, nativeStacks = stat

        if nativeStacks is not None:
            hang_stats.append({
                'name': thread_name,
                'hangs': [
                    {
                        'histogram': {'values': {'64': h[0], '128': h[1], '256': h[2]}},
                        'stack': s,
                        'nativeStack': n
                    } for s, h, n in zip(stacks, histograms, nativeStacks)
                ]
            })
        else:
            hang_stats.append({
                'name': thread_name,
                'hangs': [
                    {
                        'histogram': {'values': {'64': h[0], '128': h[1], '256': h[2]}},
                        'stack': s,
                    } for s, h in zip(stacks, histograms)
                ]
            })

    return {
        'environment/system/os/name': os,
        'application/buildId': build_id,
        'payload/info/subsessionLength': subsession_length,
        'payload/childPayloads': [],
        'payload/threadHangStats': hang_stats
    }

def create_child_ping(os, build_id, subsession_length, child_stats):
    child_payloads = []
    for child_stat in child_stats:
        hang_stats = []

        for thread_name, stacks, histograms, nativeStacks in child_stat:

            if nativeStacks is not None:
                hang_stats.append({
                    'name': thread_name,
                    'hangs': [
                        {
                            'histogram': {'values': {'64': h[0], '128': h[1], '256': h[2]}},
                            'stack': s,
                            'nativeStack': n
                        } for s, h, n in zip(stacks, histograms, nativeStacks)
                    ]
                })
            else:
                hang_stats.append({
                    'name': thread_name,
                    'hangs': [
                        {
                            'histogram': {'values': {'64': h[0], '128': h[1], '256': h[2]}},
                            'stack': s,
                        } for s, h in zip(stacks, histograms)
                    ]
                })
        child_payloads.append({'threadHangStats': hang_stats})

    return {
        'environment/system/os/name': os,
        'application/buildId': build_id,
        'payload/info/subsessionLength': subsession_length,
        'payload/childPayloads': child_payloads,
        'payload/threadHangStats': []
    }

# builds
# --------------
b_1 = '20170317987654321'
# b_2 is on the same day as build 1
b_2 = '20170317123456789'
# b_3 is on a different day
b_3 = '20170316123456789'

# stacks
# --------------
# stack 0 is a special case of an empty pseudo-stack. We want to ignore these
s_0 = []
s_1 = ['stack1', 'topframe1']
# stack 2 has the same top frame as stack 1 (topframe1)
s_2 = ['stack2', 'topframe1']
# stack 3 has a different top frame
s_3 = ['stack3', 'topframe2']
# stack 4 has the same top frame as stack 3 (topframe2)
s_4 = ['stack4', 'topframe2']

# native stacks
# --------------
n_1 = {
  'memoryMap': [
    ['xul.pdb', 'native1']
  ],
  'stacks': [
    [[ 0, 11111 ],[-1, 11112]]
  ]
}
n_2 = {
  'memoryMap': [
    ['xul.pdb', 'native2']
  ],
  'stacks': [
    [[ 0, 22222 ],[-1, 22223]]
  ]
}
n_3 = {
  'memoryMap': [
    ['xul.pdb', 'native3']
  ],
  'stacks': [
    [[ 0, 33333 ],[-1, 33334]]
  ]
}

# threads
# --------------
t_1 = 'Gecko'
t_2 = 'Gecko_Child'
t_3 = 'NotGecko1'
t_4 = 'NotGecko2'

windows = 'Windows_NT'
not_windows = 'linux'

def simple_data():
    raw_data = [
        (windows,     b_1, 100, [
            (t_1, [s_1, s_2, s_0], [(1, 2, 3), (3, 2, 1), (0, 1, 0)], None),
            (t_4, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
        ]), # second thread (t_4) should be in a different thread

        (windows,     b_2, 200, [
            (t_1, [s_3, s_2], [(1, 3, 2), (3, 4, 5)], None)
        ]),

        (windows,     b_2, 0, [
            (t_1, [s_3, s_2], [(1, 3, 2), (3, 4, 5)], None)
        ]), # should be excluded due to 0 usage hours

        (not_windows, b_2, 200, [
            (t_1, [s_3, s_2], [(7, 8, 9), (6, 7, 8)], None)
        ]), # should be ignored

        (windows,     b_3, 100, [
            (t_1, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
        ]), # should be in a different date

        (windows,     b_1, 100, [
            (t_3, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
        ]), # should be in a different thread
    ]

    return map(lambda raw: create_parent_ping(*raw), raw_data)

def child_payloads_data():
    raw_data = [
        (windows,     b_1, 100, [
            [
                (t_2, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
            ]
        ]),

        (windows,     b_2, 200, [
            [
                (t_2, [s_2, s_3], [(3, 2, 3), (1, 2, 1)], None)
            ],
            [
                (t_2, [s_3, s_2], [(3, 1, 1), (4, 2, 2)], None)
            ]
        ]),

        (windows,     b_1, 0, [
            [
                (t_2, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
            ]
        ]), # should be excluded due to 0 usage hours

        (not_windows, b_2, 200, [
            [
                (t_2, [s_3, s_2], [(7, 8, 9), (6, 7, 8)], None)
            ]
        ]), # should be ignored

        (windows,     b_3, 100, [
            [
                (t_2, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
            ]
        ]), # should be in a different date

        (windows,     b_1, 100, [
            [
                (t_3, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], None)
            ]
        ]), # should be in a different thread
    ]

    return map(lambda raw: create_child_ping(*raw), raw_data)

def native_stack_payloads_data():
    raw_data = [
        (windows,     b_1, 100, [
            (t_1, [s_1, s_2], [(1, 2, 3), (3, 2, 1)], [n_1, n_2])
        ]),

        (windows,     b_2, 200, [
            (t_1, [s_3, s_2], [(1, 3, 2), (3, 4, 5)], [n_1, n_3])
        ]),
    ]

    return map(lambda raw: create_parent_ping(*raw), raw_data)

@pytest.fixture
def simple_rdd(spark_context):
    return spark_context.parallelize(simple_data())

@pytest.fixture
def child_rdd(spark_context):
    return spark_context.parallelize(child_payloads_data())

@pytest.fixture
def native_rdd(spark_context):
    return spark_context.parallelize(native_stack_payloads_data())

# Tests
def test_simple_transform(simple_rdd):
    transformed = transform_pings(simple_rdd)
    actual = transformed['20170317']['Gecko']

    assert '20170316' in transformed
    assert 'NotGecko1' in transformed['20170317']
    assert 'NotGecko2' in transformed['20170317']

    expected = {
        'topframe1': {
            'stacks': [
                ((('stack2', 'topframe1'), None, None), {
                    'hang_ms_per_hour': 345.60, # ((2 * 128 + 1 * 256) + (4 * 128 + 5 * 256)) / (400 / 60)
                    'hang_count_per_hour': 1.80 # ((2 + 1) + (4 + 5)) / (400 / 60)
                }),
                ((('stack1', 'topframe1'), None, None), {
                    'hang_ms_per_hour': 153.60, # (2 * 128 + 3 * 256) / (400 / 60)
                    'hang_count_per_hour': 0.75 # (2 + 3) / (400 / 60)
                }),
            ],
            'hang_ms_per_hour': 345.60 + 153.60,
            'hang_count_per_hour': 1.80 + 0.75,
        },
        'topframe2': {
            'stacks': [
                ((('stack3', 'topframe2'), None, None), {
                    'hang_ms_per_hour': 134.40, # (3 * 128 + 2 * 256) / (400 / 60)
                    'hang_count_per_hour': 0.75 # (3 + 2) / (400 / 60)
                }),
            ],
            'hang_ms_per_hour': 134.40, # (3 * 128 + 2 * 256) / (400 / 60)
            'hang_count_per_hour': 0.75 # (3 + 2) / (400 / 60)
        },
        'empty_pseudo_stack': {
            'stacks': [
                (((), None, None), {
                    'hang_ms_per_hour': 19.20, # (1 * 128) / (400 / 60)
                    'hang_count_per_hour': 0.15 # (1) / (400 / 60)
                }),
            ],
            'hang_ms_per_hour': 19.20, # (1 * 128) / (400 / 60)
            'hang_count_per_hour': 0.15 # (1) / (400 / 60)
        },
    }

    assert_deep_equality(actual, expected)

def test_child_transform(child_rdd):
    transformed = transform_pings(child_rdd)
    actual = transformed['20170317']['Gecko_Child']

    assert '20170316' in transformed
    assert 'NotGecko1' in transformed['20170317']

    # kept all the numbers the same, since the second child entry is the same
    # as the second parent entry, just broken into to processes
    expected = {
        'topframe1': {
            'stacks': [
                ((('stack2', 'topframe1'), None, None), {
                    'hang_ms_per_hour': 345.60, # ((2 * 128 + 1 * 256) + (4 * 128 + 5 * 256)) / (400 / 60)
                    'hang_count_per_hour': 1.80 # ((2 + 1) + (4 + 5)) / (400 / 60)
                }),
                ((('stack1', 'topframe1'), None, None), {
                    'hang_ms_per_hour': 153.60, # (2 * 128 + 3 * 256) / (400 / 60)
                    'hang_count_per_hour': 0.75 # (2 + 3) / (400 / 60)
                }),
            ],
            'hang_ms_per_hour': 345.60 + 153.60,
            'hang_count_per_hour': 1.80 + 0.75,
        },
        'topframe2': {
            'stacks': [
                ((('stack3', 'topframe2'), None, None), {
                    'hang_ms_per_hour': 134.40, # (3 * 128 + 2 * 256) / (400 / 60)
                    'hang_count_per_hour': 0.75 # (3 + 2) / (400 / 60)
                }),
            ],
            'hang_ms_per_hour': 134.40, # (3 * 128 + 2 * 256) / (400 / 60)
            'hang_count_per_hour': 0.75 # (3 + 2) / (400 / 60)
        }
    }

    assert_deep_equality(actual, expected)

def test_native_transform(native_rdd):
    transformed = transform_pings(native_rdd)
    actual = transformed['20170317']['Gecko']

    expected = {
        'topframe1': {
            'stacks': [
                ((('stack2', 'topframe1'), (('xul.pdb', 'native3'),), (( 0, 33333 ),(-1, 33334))), {
                    'hang_ms_per_hour': 358.40, # (4 * 128 + 5 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.80 # (4 + 5) / (300 / 60)
                }),
                ((('stack1', 'topframe1'), (('xul.pdb', 'native1'),), (( 0, 11111 ),(-1, 11112))), {
                    'hang_ms_per_hour': 204.80, # (2 * 128 + 3 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.00 # (2 + 3) / (300 / 60)
                }),
                ((('stack2', 'topframe1'), (('xul.pdb', 'native2'),), (( 0, 22222 ),(-1, 22223))), {
                    'hang_ms_per_hour': 102.40, # (2 * 128 + 1 * 256) / (300 / 60)
                    'hang_count_per_hour': 0.60 # (2 + 1) / (300 / 60)
                }),
            ],
            'hang_ms_per_hour': 358.40 + 204.80 + 102.40,
            'hang_count_per_hour': 1.80 + 1.00 + 0.60,
        },
        'topframe2': {
            'stacks': [
                ((('stack3', 'topframe2'), (('xul.pdb', 'native1'),), (( 0, 11111 ),(-1, 11112))), {
                    'hang_ms_per_hour': 179.20, # (3 * 128 + 2 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.00 # (3 + 2) / (300 / 60)
                }),
            ],
            'hang_ms_per_hour': 179.20, # (3 * 128 + 2 * 256) / (300 / 60)
            'hang_count_per_hour': 1.00 # (3 + 2) / (300 / 60)
        }
    }

    assert_deep_equality(actual, expected)

def test_symbolicate_stacks(native_rdd):
    transformed = transform_pings(native_rdd)

    config = {
        'symbol_server_url': "https://s3-us-west-2.amazonaws.com/org.mozilla.crash-stats.symbols-public/v1/"
    }
    # NOTE: this makes an HTTP call - we could fake that, but I think it's most useful
    # to keep the transformation as close as possible to what's actually going on
    symbolicate_stacks(transformed, config)

    actual = transformed['20170317']['Gecko']

    expected = {
        'topframe1': {
            'stacks': [
                ((('stack2', 'topframe1'), [ "0x8235 (in xul.pdb)", 33334]), {
                    'hang_ms_per_hour': 358.40, # (4 * 128 + 5 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.80 # (4 + 5) / (300 / 60)
                }),
                ((('stack1', 'topframe1'), ["0x2b67 (in xul.pdb)", 11112]), {
                    'hang_ms_per_hour': 204.80, # (2 * 128 + 3 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.00 # (2 + 3) / (300 / 60)
                }),
                ((('stack2', 'topframe1'), ["0x56ce (in xul.pdb)", 22223]), {
                    'hang_ms_per_hour': 102.40, # (2 * 128 + 1 * 256) / (300 / 60)
                    'hang_count_per_hour': 0.60 # (2 + 1) / (300 / 60)
                }),
            ],
            'hang_ms_per_hour': 358.40 + 204.80 + 102.40,
            'hang_count_per_hour': 1.80 + 1.00 + 0.60,
        },
        'topframe2': {
            'stacks': [
                ((('stack3', 'topframe2'), ["0x2b67 (in xul.pdb)", 11112]), {
                    'hang_ms_per_hour': 179.20, # (3 * 128 + 2 * 256) / (300 / 60)
                    'hang_count_per_hour': 1.00 # (3 + 2) / (300 / 60)
                }),
            ],
            'hang_ms_per_hour': 179.20, # (3 * 128 + 2 * 256) / (300 / 60)
            'hang_count_per_hour': 1.00 # (3 + 2) / (300 / 60)
        }
    }

    assert_deep_equality(actual, expected)

def test_real_stacks():
    real_stacks = {
        ('firefox.pdb', 'C836665D4FCC4CE5AF302983CBD45DA62'): [39473, 7133, 28686, 23327],
        ('ntdll.pdb', '54F631A12F8A428AAC8CD5D273638DB82'): [178225, 12345]
    }

    config = {
        'symbol_server_url': "https://s3-us-west-2.amazonaws.com/org.mozilla.crash-stats.symbols-public/v1/"
    }
    actual = process_modules(real_stacks, config)
    expected = {
        ('C836665D4FCC4CE5AF302983CBD45DA62', 39473): 'content_process_main(mozilla::Bootstrap *,int,char * * const) (in firefox.pdb)',
        ('C836665D4FCC4CE5AF302983CBD45DA62', 7133): 'wmain (in firefox.pdb)',
        ('C836665D4FCC4CE5AF302983CBD45DA62', 28686): 'wmain (in firefox.pdb)',
        ('C836665D4FCC4CE5AF302983CBD45DA62', 23327): '__scrt_common_main_seh (in firefox.pdb)',
        ('54F631A12F8A428AAC8CD5D273638DB82', 178225): 'RtlUserThreadStart (in ntdll.pdb)',
        ('54F631A12F8A428AAC8CD5D273638DB82', 12345): 'RtlQueryRegistryValues (in ntdll.pdb)',
    }

    assert actual == expected

import time

def test_fetch_URLs():
    config = {
        'symbol_server_url': "https://s3-us-west-2.amazonaws.com/org.mozilla.crash-stats.symbols-public/v1/"
    }

    module_infos = [
        (
            "ntdll.pdb",
            "F0164DA71FAF4765B8F3DB4F2D7650EA2"
        ),
        (
            "firefox.pdb",
            "C836665D4FCC4CE5AF302983CBD45DA62"
        ),
        (
            "ntdll.pdb",
            "0A2571A3E36A4F909B719773CC176B032"
        ),
        (
            "ntdll.pdb",
            "54F631A12F8A428AAC8CD5D273638DB82"
        ),
        (
            "kernelbase.pdb",
            "A0DE635BD84C4850B0355973EC7F00831"
        ),
    ]

    URLs = [get_file_URL(module, config) for module in module_infos]

    pool = eventlet.GreenPool()

    for result in pool.imap(fetch_URL, URLs):
        pass
