from pathlib import Path
from uuid import uuid4


MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
UPLOAD_ROOT = Path(__file__).resolve().parents[1] / 'static' / 'upload'


def get_default_img():
    return '/static/upload/noimg.jpg'


def upload(uploaded_file, package):
    if package != 'faceimg':
        raise ValueError('Unsupported upload category')
    extension = Path(uploaded_file.name or '').suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError('Only JPG, PNG, GIF, and WEBP images are allowed')
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValueError('Image must be 5 MB or smaller')

    target_dir = UPLOAD_ROOT / package
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}{extension}'
    target = target_dir / filename
    with target.open('xb') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return f'/static/upload/{package}/{filename}'


def delfile(path):
    if not path or not path.startswith('/static/upload/'):
        return
    candidate = (UPLOAD_ROOT.parent.parent / path.lstrip('/')).resolve()
    upload_root = UPLOAD_ROOT.resolve()
    if candidate == upload_root or upload_root not in candidate.parents:
        return
    if candidate.name == 'noimg.jpg':
        return
    if candidate.is_file():
        candidate.unlink()
