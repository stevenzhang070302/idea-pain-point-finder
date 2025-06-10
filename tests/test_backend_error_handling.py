import os
import sys
import json
import asyncio
import sqlite3
import tempfile

import pytest

# Import backend module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3', 'backend'))
import backend
from fastapi import BackgroundTasks, HTTPException

class DummyWorkflow:
    def compile(self):
        return self
    def invoke(self, state):
        return {'final_output': {'topic': state['topic'], 'clusters': []}}

def setup_temp_db(monkeypatch):
    temp_dir = tempfile.TemporaryDirectory()
    db_path = os.path.join(temp_dir.name, 'temp.db')
    monkeypatch.setattr(backend, 'DATABASE_PATH', db_path)
    backend.init_database()
    return temp_dir, db_path

def test_run_pain_analysis_missing_env(monkeypatch):
    temp_dir, db_path = setup_temp_db(monkeypatch)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
    monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
    monkeypatch.setattr(backend, 'create_workflow', lambda: DummyWorkflow())

    asyncio.run(backend.run_pain_analysis('test', 'testhash'))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT results FROM analysis_results WHERE topic_hash=?', ('testhash',))
    row = cursor.fetchone()
    conn.close()
    temp_dir.cleanup()

    assert row is not None
    data = json.loads(row[0])
    assert 'error' in data

def test_start_analysis_missing_env(monkeypatch):
    temp_dir, db_path = setup_temp_db(monkeypatch)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
    monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
    req = backend.AnalysisRequest(topic='x', save_results=False)

    with pytest.raises(HTTPException):
        asyncio.run(backend.start_analysis(req, BackgroundTasks()))

    temp_dir.cleanup()
