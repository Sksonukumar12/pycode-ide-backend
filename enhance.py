import os
import uuid
import cv2
from gfpgan import GFPGANer
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ---- Load Models ----
face_enhancer = GFPGANer(
    model_path="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
    upscale=2,
    arch="clean",
    channel_multiplier=2,
    bg_upsampler=None
)

rrdbnet = RRDBNet(
    num_in_ch=3,
    num_out_ch=3,
    num_feat=64,
    num_block=23,
    num_grow_ch=32,
    scale=4
)

upscaler = RealESRGANer(
    scale=4,
    model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.4.6/RealESRGAN_x4plus.pth",
    model=rrdbnet,
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False
)

def enhance_image(image_path):
    img = cv2.imread(image_path)

    # Face enhancement
    _, _, face_img = face_enhancer.enhance(
        img, has_aligned=False, only_center_face=False, paste_back=True
    )

    # Upscale
    upscaled, _ = upscaler.enhance(face_img, outscale=4)

    result_name = f"{uuid.uuid4()}.jpg"
    result_path = os.path.join(RESULT_DIR, result_name)
    cv2.imwrite(result_path, upscaled)

    return result_path
