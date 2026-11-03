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
MATKUL_URL = os.getenv('MATKUL_URL', 'http://matkul-service:5000')

class Mahasiswa(db.Model):
    __tablename__ = 'mahasiswa'
    nim = db.Column(db.String(15), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    angkatan = db.Column(db.Integer)
    
    def to_dict(self):
        return {'nim': self.nim, 'nama': self.nama, 'email': self.email, 'angkatan': self.angkatan}

class Krs(db.Model):
    __tablename__ = 'krs'
    id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(db.String(15), db.ForeignKey('mahasiswa.nim', ondelete='CASCADE'), nullable=False)
    kode_mk = db.Column(db.String(10), nullable=False)
    __table_args__ = (db.UniqueConstraint('nim', 'kode_mk'),)

def error(pesan, kode):
    return jsonify({'error': pesan}), kode

@app.get('/health')
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'service': 'mahasiswa-service', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.get('/mahasiswa')
def list_mhs():
    data = Mahasiswa.query.order_by(Mahasiswa.nim).all()
    return jsonify([m.to_dict() for m in data])

@app.post('/mahasiswa')
def create_mhs():
    d = request.get_json(silent=True) or {}
    if not d.get('nim') or not d.get('nama'):
        return error('nim dan nama wajib diisi', 400)
    m = Mahasiswa(nim=d['nim'], nama=d['nama'], email=d.get('email'), angkatan=d.get('angkatan'))
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error('NIM sudah terdaftar', 409)
    return jsonify(m.to_dict()), 201

@app.get('/mahasiswa/<nim>')
def get_mhs(nim):
    m = db.session.get(Mahasiswa, nim)
    if not m:
        return error('mahasiswa tidak ditemukan', 404)
    return jsonify(m.to_dict())

@app.put('/mahasiswa/<nim>')
def update_mhs(nim):
    m = db.session.get(Mahasiswa, nim)
    if not m:
        return error('mahasiswa tidak ditemukan', 404)
    d = request.get_json(silent=True) or {}
    m.nama = d.get('nama', m.nama)
    m.email = d.get('email', m.email)
    m.angkatan = d.get('angkatan', m.angkatan)
    db.session.commit()
    return jsonify(m.to_dict())

@app.delete('/mahasiswa/<nim>')
def delete_mhs(nim):
    m = db.session.get(Mahasiswa, nim)
    if not m:
        return error('mahasiswa tidak ditemukan', 404)
    db.session.delete(m)
    db.session.commit()
    return '', 204

@app.get('/mahasiswa/<nim>/matkul')
def list_krs(nim):
    if not db.session.get(Mahasiswa, nim):
        return error('mahasiswa tidak ditemukan', 404)
    krs_records = Krs.query.filter_by(nim=nim).all()
    if not krs_records:
        return jsonify([])
        
    kode_list = [k.kode_mk for k in krs_records]
    matkul_map = {}
    try:
        r = requests.post(f'{MATKUL_URL}/matkul/batch', json={'kode': kode_list}, timeout=3)
        if r.ok:
            for item in r.json():
                matkul_map[item['kode']] = item
    except requests.RequestException:
        pass
        
    hasil = []
    for k in krs_records:
        item = {'kode_mk': k.kode_mk}
        if k.kode_mk in matkul_map:
            item.update(matkul_map[k.kode_mk])
        else:
            item['nama'] = '(Detail matkul tidak tersedia)'
            item['sks'] = '-'
            item['catatan'] = 'Detail matkul tidak tersedia atau telah dihapus'
        hasil.append(item)
    return jsonify(hasil)

@app.post('/mahasiswa/<nim>/matkul')
def ambil_matkul(nim):
    if not db.session.get(Mahasiswa, nim):
        return error('mahasiswa tidak ditemukan', 404)
    d = request.get_json(silent=True) or {}
    kode = d.get('kode_mk')
    if not kode:
        return error('kode_mk wajib diisi', 400)
    try:
        r = requests.get(f'{MATKUL_URL}/matkul/{kode}', timeout=3)
    except requests.RequestException:
        return error('matkul-service tidak dapat dihubungi', 503)
    if r.status_code == 404:
        return error('mata kuliah tidak ditemukan', 404)
    db.session.add(Krs(nim=nim, kode_mk=kode))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error('mata kuliah sudah diambil', 409)
    return jsonify({'nim': nim, 'kode_mk': kode, 'pesan': 'berhasil'}), 201

@app.delete('/mahasiswa/<nim>/matkul/<kode_mk>')
def batal_matkul(nim, kode_mk):
    k = Krs.query.filter_by(nim=nim, kode_mk=kode_mk).first()
    if not k:
        return error('data pengambilan tidak ditemukan', 404)
    db.session.delete(k)
    db.session.commit()
    return '', 204

@app.delete('/internal/krs/matkul/<kode_mk>')
def cleanup_krs_matkul(kode_mk):
    Krs.query.filter_by(kode_mk=kode_mk).delete()
    db.session.commit()
    return jsonify({'pesan': f'KRS untuk {kode_mk} berhasil dibersihkan'}), 200

def init_db():
    for _ in range(30):
        try:
            with app.app_context():
                db.create_all()
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError('database tidak tersedia')

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
