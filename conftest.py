"""Evidence logging for wishlist and comparison scenarios."""
import hashlib
import importlib.metadata as metadata
import json
import platform
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).parent
DESIGN = {s['scenario_id']: s for s in json.loads((ROOT / 'scenario-design.json').read_text())}


def now():
    return datetime.now(ZoneInfo('Australia/Sydney')).isoformat()


def pytest_addoption(parser):
    parser.addoption('--operator', default=None, help='Name of the person running this execution')
    parser.addoption('--evidence-dir', default='evidence')


def pytest_configure(config):
    # Collection checks import the code without starting a run or creating evidence.
    if config.getoption('collectonly'):
        return
    if not config.getoption('--operator'):
        raise pytest.UsageError('Supply --operator with the actual test runner name')
    stamp = datetime.now(ZoneInfo('Australia/Sydney')).strftime('%Y%m%d-%H%M%S')
    config.run_dir = Path(config.getoption('--evidence-dir')) / (stamp + '-' + uuid.uuid4().hex[:6])
    config.run_dir.mkdir(parents=True, exist_ok=False)
    config.records = {}
    config.environment = {'started': now(), 'operator': config.getoption('--operator'),
        'system': platform.system(), 'os_version': platform.mac_ver()[0] or platform.release(),
        'architecture': platform.machine(), 'python': platform.python_version(),
        **{n: metadata.version(n) for n in ['pytest', 'playwright', 'pytest-playwright']},
        'viewport': '1280x900', 'locale': 'en-US', 'timezone': 'Australia/Sydney',
        'site': 'https://opencart.abstracta.us/', 'headless': not config.getoption('headed'),
        'demo_orders_enabled': False, 'source_sha256': {}}
    for p in [*ROOT.glob('*.py'), *ROOT.joinpath('tests').glob('*.py'), ROOT / 'scenario-design.json', ROOT / 'requirements.txt']:
        rel = p.relative_to(ROOT)
        config.environment['source_sha256'][str(rel)] = hashlib.sha256(p.read_bytes()).hexdigest()
        dest = config.run_dir / 'source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    (config.run_dir / 'environment.json').write_text(json.dumps(config.environment, indent=2))


def pytest_collection_modifyitems(items):
    items.sort(key=lambda item: item.callspec.params.get('scenario', ''))


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    return {**browser_context_args, 'viewport': {'width': 1280, 'height': 900}, 'locale': 'en-US'}


@pytest.fixture
def record(page, request, scenario):
    page.set_default_timeout(15000)
    rec = {**DESIGN[scenario], 'operator': request.config.getoption('--operator'), 'started': now(),
           'input': {}, 'observations': {}, 'status': 'Not run', 'assertions_completed': False}
    request.node.scenario_record = rec
    request.config.records[scenario] = rec
    request.config.environment['browser_version'] = page.context.browser.version
    page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield rec
    try:
        rec['url'] = page.url
        expect(page.locator('.collapsing')).to_have_count(0)
        page.locator('#content').screenshot(path=str(request.config.run_dir / (scenario + '-content.png')))
        rec['document_screenshot'] = scenario + '-content.png'
        page.screenshot(path=str(request.config.run_dir / (scenario + '.png')), full_page=True)
        rec['screenshot'] = scenario + '.png'
        rec['page_text'] = page.locator('body').inner_text(timeout=3000)[:14000]
        (request.config.run_dir / (scenario + '.html')).write_text(page.content())
    except Exception as e:
        rec['capture_error'] = str(e)[:1000]
    page.context.tracing.stop(path=str(request.config.run_dir / (scenario + '-trace.zip')))
    rec['finished'] = now()
    (request.config.run_dir / (scenario + '.json')).write_text(json.dumps(rec, indent=2))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    rec = getattr(item, 'scenario_record', None)
    if rec is None:
        return
    if report.when == 'call':
        rec['status'] = 'Pass' if report.passed else 'Blocked' if report.skipped else 'Fail' if call.excinfo and call.excinfo.errisinstance(AssertionError) else 'Error'
        rec['assertions_completed'] = report.passed
        if not report.passed:
            rec['error'] = str(call.excinfo.value) if call.excinfo else str(report.longrepr)
    elif report.failed:
        rec['status'] = 'Error'
        rec['error'] = str(report.longrepr)


def pytest_sessionfinish(session):
    if session.config.getoption('collectonly'):
        return
    config = session.config
    config.environment['finished'] = now()
    records = list(config.records.values())
    counts = {status: sum(r['status'] == status for r in records) for status in ['Pass', 'Fail', 'Error', 'Blocked', 'Not run']}
    (config.run_dir / 'environment.json').write_text(json.dumps(config.environment, indent=2))
    (config.run_dir / 'summary.json').write_text(json.dumps({'counts': counts, 'records': records}, indent=2))
    print('\nEvidence:', config.run_dir.resolve())
