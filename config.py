# data configs
shapenet_path = '/Users/liweiyu/MyCodes/shapenet-v2'
shapenet_cate = {
                'table': '04379243',
                'jar': '03593526',
                'skateboard': '04225987',
                'car': '02958343',
                'bottle': '02876657',
                'tower': '04460130',
                'chair': '03001627',
                'bookshelf': '02871439',
                'camera': '02942699',
                'airplane': '02691156',
                'laptop': '03642806',
                'basket': '02801938',
                'sofa': '04256520',
                'knife': '03624134',
                'can': '02946921',
                'rifle': '04090263',
                'train': '04468005',
                'pillow': '03938244',
                'lamp': '03636649',
                'trash bin': '02747177',
                'mailbox': '03710193',
                'watercraft': '04530566',
                'motorbike': '03790512',
                'dishwasher': '03207941',
                'bench': '02828884',
                'pistol': '03948459',
                'rocket': '04099429',
                'loudspeaker': '03691459',
                'file cabinet': '03337140',
                'bag': '02773838',
                'cabinet': '02933112',
                'bed': '02818832',
                'birdhouse': '02843684',
                'display': '03211117',
                'piano': '03928116',
                'earphone': '03261776',
                'telephone': '04401088',
                'stove': '04330267',
                'microphone': '03759954',
                'bus': '02924116',
                'mug': '03797390',
                'remote': '04074963',
                'bathtub': '02808440',
                'bowl': '02880940',
                'keyboard': '03085013',
                'guitar': '03467517',
                'washer': '04554684',
                'bicycle': '02834778',
                'faucet': '03325088',
                'printer': '04004475',
                'cap': '02954340',
                'clock': '03046257',
                'helmet': '03513137',
                'flowerpot': '03991062',
                'microwaves': '03761084'
                }
render_cate = ['car']
# blender configs
blender_path = '/Applications/Blender.app/Contents/MacOS/blender'

# render configs
render_engine = 'CYCLES' # 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'
film_transparent = True
sample_type = 'sphere' # 'sphere', 'side'
num_samples = 100
scale = 2
use_half = True # is use half, num_sample is divided by 2


# output image configs
x_res = 256
y_res = 256
res_percentage = 100
out_path = 'output'

## rgb
rgb_out_path = 'rgb'
rgb_color_mode = 'RGBA'
rgb_color_depth = '16'
rgb_file_format = 'PNG'

## depth 
depth_offset = [-0.1]
depth_scale = [0.5]
depth_out_path = 'depth'
depth_color_mode = 'RGBA'
depth_file_format = 'PNG'

## normal
normal_out_path = 'normal'
normal_color_mode = 'RGBA'
normal_file_format = 'PNG'

## albedo
albedo_out_path = 'albedo'
albedo_color_mode = 'RGBA'
albedo_file_format = 'PNG'

