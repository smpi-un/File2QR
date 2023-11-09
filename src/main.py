
import os
import zipfile
import qrcode
import re
import glob
from typing import Optional
import cv2
import base64
import shutil
import argparse
import tempfile
import tarfile




def make_qrcode(file_path: str, output_dir: str) -> list[str]:
  unit = 2000
  with open(file_path, 'rb') as fp:
    file_data = base64.b64encode(fp.read()).decode()

  res = []
  for i in range(1+int(len(file_data)/unit)):
    out_data = file_data[i*unit:(i+1)*unit]
    
    img = qrcode.make(out_data)
    output_path = os.path.join(output_dir, f"{os.path.basename(file_path)}.{i}.png")
    if not os.path.exists(os.path.dirname(output_path)):
      os.makedirs(os.path.dirname(output_path))
    img.save(output_path)
    res.append(output_path)
  return res

def compress_zip(src_path: str, dst_path: str):
  if not os.path.exists(os.path.dirname(dst_path)):
    os.makedirs(os.path.dirname(dst_path))

  if os.path.isdir(src_path):
    # 'zip' 形式で圧縮する
    shutil.make_archive(os.path.splitext(dst_path)[0], 'zip', src_path)
  else:
    with zipfile.ZipFile(dst_path, 'w',
                      compression=zipfile.ZIP_DEFLATED,
                      compresslevel=9) as zf:
      zf.write(src_path, arcname=os.path.basename(src_path))

def compress_xz(src_path: str, dst_path: str):
  if not os.path.exists(os.path.dirname(dst_path)):
    os.makedirs(os.path.dirname(dst_path))
  with tarfile.open(dst_path, 'w:xz') as tfile:
      tfile.add(src_path, arcname='')



def conv_qr(input_path: str, format: str = 'xz', output_dir: str = '') -> list[str]:
  input_path = os.path.abspath(input_path)
  # 一時ファイルを作成します
  temp = tempfile.mktemp()

  if format == 'xz' or format is None:
    zipfile_path = os.path.join(temp, f'{os.path.basename(input_path)}.tar.xz')
    compress_xz(input_path, zipfile_path)
  elif format == 'zip':
    zipfile_path = os.path.join(temp, f'{os.path.basename(input_path)}.zip')
    compress_zip(input_path, zipfile_path)
  else:
    return None

  res = make_qrcode(zipfile_path, output_dir)
  os.remove(zipfile_path)
  return res

def unconv_qr(input_path: str, output_dir: str = '') -> Optional[str]:
  reg = re.compile(r'(.*)\.[0-9]+\.(.+)')
  if reg.match(input_path) is None:
    return None
  ptn = reg.sub(r'\1.*.\2', input_path)
  out_name = reg.sub(r'\1', input_path)

  data = bytes()
  for file in glob.glob(ptn):
    read_data = read_qr_code(file)
    if read_data is not None:
      data += read_data
  output_path = os.path.join(output_dir, out_name)

  if not os.path.exists(os.path.dirname(output_path)):
    os.makedirs(os.path.dirname(output_path))
  with open(output_path, 'wb') as fp:
    fp.write(data)
  return output_path

# QRコードを読み取り、バイナリデータを取得する関数
def read_qr_code(image_path) -> Optional[bytes]:
    detector = cv2.QRCodeDetector()
    # 画像ファイルを読み込む
    image = cv2.imread(image_path)

    # QRコードをデコード
    data, bbox, straight_qrcode = detector.detectAndDecode(image)
    # decoded_objects = pyzbar.pyzbar.decode(image)
    if bbox is not None:
        return base64.b64decode(data)
    else:
        return None



if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  subparsers = parser.add_subparsers()

  # First sub-command is 'greet' which is used to greet the user
  toqr_parser = subparsers.add_parser('toqr', help='')
  toqr_parser.add_argument('--out', help='')
  toqr_parser.add_argument('--format', help='')
  toqr_parser.add_argument('in', help='')
  toqr_parser.set_defaults(func=lambda x:conv_qr(x.__dict__['in'], x.format, x.out))

  # Second sub-command is 'sum' used to add numbers
  fromqr_parser = subparsers.add_parser('fromqr', help='')
  fromqr_parser.add_argument('--out', help='')
  fromqr_parser.add_argument('in', help='')
  fromqr_parser.set_defaults(func=lambda x:unconv_qr(x.__dict__['in'], x.__dict__['out']))


  args = parser.parse_args()
  if not vars(args):  # Check if 'args' is empty
    parser.print_help()
    parser.exit()
  args.func(args)  # Call the function associated with the chosen sub-command

  # if False:
  #   file_path = r'./KMSearch.7z.0.png'
  #   output_dir = './'
  #   unconv_qr(file_path, output_dir)
  # else:
  #   file_path = r'./README.md'
  #   # file_path = r'./pyproject.toml'
  #   output_dir = './out'
  #   # compress_zip()
  #   res = conv_qr(file_path, output_dir)
  #   print(res)

  #   res2 = unconv_qr(res[0], './test/')
  #   print(res2)

