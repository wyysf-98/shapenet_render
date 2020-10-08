import os
import bpy
import sys
import os.path as osp
abs_path = os.path.abspath(__file__)
sys.path.append(os.path.dirname(abs_path))
from mathutils import Vector, Matrix
from utils import *
from config import *
from glob import glob

class BlenderRender():
    def __init__(self):
        self.__set_sence()
        self.__set_nodes()
        self.__set_camera()
        self.__get_calibration_matrix_K_from_blender()

        print(self.K)

    def __del_all_mesh(self):
        # Delete all mesh
        bpy.ops.object.select_by_type(type="MESH")
        bpy.ops.object.delete(use_global=False)

    def __set_sence(self):
        # Delete all objects, mainly for delete default cube
        bpy.ops.object.delete()

        # Render config
        self.scene = bpy.context.scene
        self.scene.render.engine = render_engine
        self.scene.render.film_transparent = film_transparent

        # Output config
        bpy.context.view_layer.use_pass_normal = True
        bpy.context.view_layer.use_pass_diffuse_color = True

        self.scene.render.image_settings.color_mode = rgb_color_mode
        self.scene.render.image_settings.color_depth = rgb_color_depth
        self.scene.render.image_settings.file_format = rgb_file_format
        self.scene.render.resolution_x = x_res
        self.scene.render.resolution_y = y_res
        self.scene.render.resolution_percentage = res_percentage

    def __set_nodes(self):
        # Set up rendering of depth map.
        self.scene.use_nodes = True
        self.tree = self.scene.node_tree
        links = self.tree.links

        # Clear default nodes
        for n in self.tree.nodes:
            self.tree.nodes.remove(n)

        render_layers = self.tree.nodes.new('CompositorNodeRLayers')

        # Config depth node
        self.depth_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.depth_file_output.label = 'Depth Output'
        if depth_file_format == 'OPEN_EXR':
            links.new(render_layers.outputs['Depth'],
                      self.depth_file_output.inputs[0])
        else:
            # Remap as other types can not represent the full range of depth.
            remap = self.tree.nodes.new(type="CompositorNodeMapValue")
            remap.use_min = True
            remap.min[0] = depth_min
            remap.use_max = True
            remap.max[0] = depth_max
            links.new(render_layers.outputs['Depth'], remap.inputs[0])
            links.new(remap.outputs[0], self.depth_file_output.inputs[0])
        self.depth_file_output.format.file_format = depth_file_format

        # Config normal node
        self.normal_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.normal_file_output.label = 'Normal Output'
        if normal_file_format == 'OPEN_EXR':
            links.new(render_layers.outputs['Normal'],
                      self.normal_file_output.inputs[0])
        else:
            scale_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
            scale_normal.blend_type = 'MULTIPLY'
            scale_normal.use_alpha = normal_use_alpha
            scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
            links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])
            bias_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
            bias_normal.blend_type = 'ADD'
            bias_normal.use_alpha = normal_use_alpha
            bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
            links.new(scale_normal.outputs[0], bias_normal.inputs[1])
            links.new(bias_normal.outputs[0],
                      self.normal_file_output.inputs[0])
        self.normal_file_output.format.file_format = normal_file_format

        # Config albedo node
        self.albedo_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.albedo_file_output.label = 'Albedo Output'
        links.new(render_layers.outputs['DiffCol'],
                  self.albedo_file_output.inputs[0])
        self.albedo_file_output.format.file_format = albedo_file_format

        # Config base path for output
        for output_node in [self.depth_file_output, self.normal_file_output, self.albedo_file_output]:
            output_node.base_path = ''

    def __set_camera(self):
        self.cam = self.scene.objects['Camera']
        self.cam.location = (0, 1, 0)
        self.cam.data.lens = focal_len

        cam_constraint = self.cam.constraints.new(type='TRACK_TO')
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z' # TOP DOWN
        cam_constraint.up_axis = 'UP_Y'

    def __import_obj(self, obj_path):
        self.__del_all_mesh()
        bpy.ops.import_scene.obj(filepath=obj_path)

    # we could also define the camera matrix
    # https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
    def __get_calibration_matrix_K_from_blender(self):
        self.cam = self.scene.objects['Camera']
        f_in_mm = self.cam.data.lens
        scene = bpy.context.scene
        resolution_x_in_px = scene.render.resolution_x
        resolution_y_in_px = scene.render.resolution_y
        scale = scene.render.resolution_percentage / 100
        sensor_width_in_mm = self.cam.data.sensor_width
        sensor_height_in_mm = self.cam.data.sensor_height
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

        if self.cam.data.sensor_fit == 'VERTICAL':
            # the sensor height is fixed (sensor fit is horizontal),
            # the sensor width is effectively changed with the pixel aspect ratio
            s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
            s_v = resolution_y_in_px * scale / sensor_height_in_mm
        else:  # 'HORIZONTAL' and 'AUTO'
            # the sensor width is fixed (sensor fit is horizontal),
            # the sensor height is effectively changed with the pixel aspect ratio
            s_u = resolution_x_in_px * scale / sensor_width_in_mm
            s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm

        # Parameters of intrinsic calibration matrix K
        alpha_u = f_in_mm * s_u
        alpha_v = f_in_mm * s_v
        u_0 = resolution_x_in_px * scale / 2
        v_0 = resolution_y_in_px * scale / 2
        skew = 0  # only use rectangular pixels

        self.K = Matrix(((alpha_u, skew, u_0),
                    (0, alpha_v, v_0),
                    (0, 0, 1)))

    def look_at(self, obj, point):
        obj.rotation_mode = 'XYZ'
        loc_obj = obj.location
        direction = point - loc_obj
        # point the cameras '-Z' and use its 'Y' as up
        rot_quat = direction.to_track_quat('-Z', 'Y')

        obj.rotation_euler = rot_quat.to_euler()

    def get_pose(self, obj):
        obj.rotation_mode = 'QUATERNION'
        q = obj.rotation_quaternion
        print(q)

        m = np.array(
        [[1-2*q[2]*q[2]-2*q[3]*q[3], 2*q[1]*q[2]-2*q[0]*q[3],   2*q[1]*q[3]+2*q[0]*q[2],   obj.location[0]], 
        [2*q[1]*q[2]+2*q[0]*q[3],    1-2*q[1]*q[1]-2*q[3]*q[3], 2*q[2]*q[3]-2*q[0]*q[1],   obj.location[1]],
        [2*q[1]*q[3]-2*q[0]*q[2],    2*q[2]*q[3]+2*q[0]*q[1],   1-2*q[1]*q[1]-2*q[2]*q[2], obj.location[2]],
        [0,                          0,                         0,                         1]])
        print(m)

    def move_camera(self, cam_loc):
        self.cam.location = cam_loc
        self.look_at(self.cam, Vector((0.0, 0, 0)))
        self.get_pose(self.cam)

    def render(self, obj_path):
        obj_name = obj_path.split('/')[-3]

        self.__import_obj(obj_path)

        if sample_type == 'sphere':
            cam_loc = sample_sphere(num_samples, scale, use_half)
        elif sample_type == 'side':
            cam_loc = sample_side(scale)
        else:
            raise NotImplementedError(
                '{} is not implemented !!!'.format(sample_type))
        
        out_paths = []
        for i, loc in enumerate(cam_loc):
            self.move_camera(loc)
            self.scene.render.filepath = osp.join(
                out_path, rgb_out_path, obj_name, '{}.png'.format(i))
            self.depth_file_output.file_slots[0].path = osp.join(
                out_path, depth_out_path, obj_name, str(i))
            self.depth_file_output.file_slots[0].use_node_format = False
            self.normal_file_output.file_slots[0].path = osp.join(
                out_path, normal_out_path, obj_name, str(i))
            self.albedo_file_output.file_slots[0].path = osp.join(
                out_path, albedo_out_path, obj_name, str(i))
            out_paths.extend([
                osp.join(out_path, depth_out_path, obj_name, str(i)),
                osp.join(out_path, normal_out_path, obj_name, str(i)),
                osp.join(out_path, albedo_out_path, obj_name, str(i)),
            ])
            bpy.ops.render.render(write_still=True)
        return out_paths

if __name__ == "__main__":
    if not osp.exists(out_path):
        os.makedirs(out_path)

    my_render = BlenderRender()
    for cate in render_cate:
        models_path = glob(
            osp.join(shapenet_path, shapenet_cate[cate], '*', 'models', 'model_normalized.obj'))
        for model_path in models_path:
            out_paths = my_render.render(model_path)
            prefix_name(out_paths)
            break