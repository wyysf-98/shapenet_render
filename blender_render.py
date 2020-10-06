import os
import bpy
import sys
import os.path as osp
abs_path = os.path.abspath(__file__)
sys.path.append(os.path.dirname(abs_path))

from glob import glob
from config import *
from utils import *
from mathutils import Vector

class BlenderRender():
    def __init__(self):
        self.__set_sence()
        self.__set_nodes()

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
        # Remap as other types can not represent the full range of depth.
        remap = self.tree.nodes.new(type="CompositorNodeMapValue")
        # Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
        remap.offset = depth_offset
        remap.size = depth_scale
        remap.use_min = True
        remap.min = [0]
        links.new(render_layers.outputs['Depth'], remap.inputs[0])
        links.new(remap.outputs[0], self.depth_file_output.inputs[0])
        self.depth_file_output.format.file_format = depth_file_format
        self.depth_file_output.format.color_mode = depth_color_mode

        # Config normal node
        scale_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
        scale_normal.blend_type = 'MULTIPLY'
        # scale_normal.use_alpha = True
        scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
        links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])
        bias_normal = self.tree.nodes.new(type="CompositorNodeMixRGB")
        bias_normal.blend_type = 'ADD'
        # bias_normal.use_alpha = True
        bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
        links.new(scale_normal.outputs[0], bias_normal.inputs[1])
        self.normal_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.normal_file_output.label = 'Normal Output'
        links.new(bias_normal.outputs[0], self.normal_file_output.inputs[0])
        self.normal_file_output.format.file_format = normal_file_format
        self.normal_file_output.format.color_mode = normal_color_mode

        # Config albedo node
        self.albedo_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.albedo_file_output.label = 'Albedo Output'
        links.new(render_layers.outputs['DiffCol'],
                  self.albedo_file_output.inputs[0])
        self.albedo_file_output.format.file_format = albedo_file_format
        self.albedo_file_output.format.color_mode = albedo_color_mode

    def look_at(self, obj, point):
        loc_obj = obj.location
        direction = point - loc_obj
        # point the cameras '-Z' and use its 'Y' as up
        rot_quat = direction.to_track_quat('-Z', 'Y')

        obj.rotation_euler = rot_quat.to_euler()

    def move_camera(self, init_loc=(0, 1, 0)):
        self.cam = self.scene.objects['Camera']
        self.cam.location = init_loc
        cam_constraint = self.cam.constraints.new(type='TRACK_TO')
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        cam_constraint.up_axis = 'UP_Y'

        self.look_at(self.cam, Vector((0.0, 0, 0)))

    def import_obj(self, obj_path):
        self.__del_all_mesh()
        bpy.ops.import_scene.obj(filepath=obj_path)

        # cur_obj = bpy.context.selected_objects[0]
        # scale = 8
        # cur_obj.scale = (scale, scale, scale)

        # for polygon in cur_obj.data.polygons:
        #     polygon.use_smooth = True
        # for mat in bpy.data.materials:
        #     mat.use_backface_culling = True

    def render(self):
        for output_node in [self.depth_file_output, self.normal_file_output, self.albedo_file_output]:
            output_node.base_path = ''

        if sample_type == 'sphere':
            cam_loc = sample_sphere(num_samples, scale, use_half)
        elif sample_type == 'side':
            cam_loc = sample_side(scale)
        else:
            raise NotImplementedError(
                '{} is not implemented !!!'.format(sample_type))

        for i, loc in enumerate(cam_loc):
            self.move_camera(loc)

            self.scene.render.filepath = osp.join(
                out_path, rgb_out_path, '{}.png'.format(i))
            self.depth_file_output.file_slots[0].path = osp.join(
                out_path, depth_out_path, '{}_'.format(i))
            self.normal_file_output.file_slots[0].path = osp.join(
                out_path, normal_out_path, '{}_'.format(i))
            self.albedo_file_output.file_slots[0].path = osp.join(
                out_path, albedo_out_path, '{}_'.format(i))

            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    if not osp.exists(out_path):
        os.makedirs(out_path)

    my_render = BlenderRender()
    for cate in render_cate:
        model_path = glob(
            osp.join(shapenet_path, shapenet_cate[cate], '*', 'models', 'model_normalized.obj'))
        my_render.import_obj(model_path[1])
        my_render.render()
