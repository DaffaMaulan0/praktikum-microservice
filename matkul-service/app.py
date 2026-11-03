import os
import time
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

MAHASISWA_URL = os.getenv('MAHASISWA_URL', 'http://mahasiswa-service:5000')

class MataKuliah(db.Model):
    __tablename__ = 'mata_kuliah'
    kode = db.Column(db.String(10), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    sks = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer)
    
    def to_dict(self):
        return {'kode': self.kode, 'nama': self.nama, 'sks': self.sks, 'semester': self.semester}

def error(pesan, kode):
    return jsonify({'error': pesan}), kode

@app.get('/health')
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'service': 'matkul-service', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.get('/matkul')
def list_mk():
    data = MataKuliah.query.order_by(MataKuliah.kode).all()
    return jsonify([m.to_dict() for m in data])

@app.post('/matkul/batch')
def batch_mk():
    d = request.get_json(silent=True) or {}
    kode_list = d.get('kode', [])
    if not isinstance(kode_list, list):
        return error('kode harus berupa array list', 400)
    if not kode_list:
        return jsonify([])
    data = MataKuliah.query.filter(MataKuliah.kode.in_(kode_list)).all()
    return jsonify([m.to_dict() for m in data])

@app.post('/matkul')
def create_mk():
    d = request.get_json(silent=True) or {}
    if not d.get('kode') or not d.get('nama') or not d.get('sks'):
        return error('kode, nama, dan sks wajib diisi', 400)
    m = MataKuliah(kode=d['kode'], nama=d['nama'], sks=d['sks'], semester=d.get('semester'))
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error('kode mata kuliah sudah ada', 409)
    return jsonify(m.to_dict()), 201

@app.get('/matkul/<kode>')
def get_mk(kode):
    m = db.session.get(MataKuliah, kode)
    if not m:
        return error('mata kuliah tidak ditemukan', 404)
    return jsonify(m.to_dict())

@app.put('/matkul/<kode>')
def update_mk(kode):
    m = db.session.get(MataKuliah, kode)
    if not m:
        return error('mata kuliah tidak ditemukan', 404)
    d = request.get_json(silent=True) or {}
    m.nama = d.get('nama', m.nama)
    m.sks = d.get('sks', m.sks)
    m.semester = d.get('semester', m.semester)
    db.session.commit()
    return jsonify(m.to_dict())

@app.delete('/matkul/<kode>')
def delete_mk(kode):
    m = db.session.get(MataKuliah, kode)
    if not m:
        return error('mata kuliah tidak ditemukan', 404)
    db.session.delete(m)
    db.session.commit()
    
    # Beritahu mahasiswa-service untuk membersihkan KRS terkait (Cascade across services)
    try:
        requests.delete(f'{MAHASISWA_URL}/internal/krs/matkul/{kode}', timeout=3)
    except requests.RequestException:
        pass
        
    return '', 204

def init_db():
    for _ in range(30):
        try:
            with app.app_context():
                db.create_all()
                if MataKuliah.query.count() == 0:
                    db.session.add_all([
                        MataKuliah(kode='IF301', nama='Sistem Terdistribusi', sks=3, semester=5),
                        MataKuliah(kode='IF302', nama='Basis Data Lanjut', sks=3, semester=5),
                        MataKuliah(kode='IF303', nama='Jaringan Komputer', sks=3, semester=4),
                    ])
                    db.session.commit()
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError('database tidak tersedia')

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
