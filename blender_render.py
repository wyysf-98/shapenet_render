import os
import bpy
import sys
import os.path as osp
abs_path = os.path.abspath(__file__)
sys.path.append(os.path.dirname(abs_path))

from config import *
from glob import glob

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
        bpy.context.scene.render.engine = render_engine
        bpy.context.scene.render.film_transparent = film_transparent

        # Output config
        bpy.context.view_layer.use_pass_normal = True
        bpy.context.view_layer.use_pass_diffuse_color = True

        bpy.context.scene.render.image_settings.color_mode = color_mode
        bpy.context.scene.render.image_settings.color_depth = color_depth
        bpy.context.scene.render.image_settings.file_format = file_format
        bpy.context.scene.render.resolution_x = x_res
        bpy.context.scene.render.resolution_y = y_res
        bpy.context.scene.render.resolution_percentage = res_percentage

    def __set_nodes(self):
        # Set up rendering of depth map.
        bpy.context.scene.use_nodes = True
        self.tree = bpy.context.scene.node_tree
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
        self.normal_file_output.format.file_format = "PNG"
        self.normal_file_output.format.color_mode = "RGBA"

        # Config albedo node
        self.albedo_file_output = self.tree.nodes.new(
            type="CompositorNodeOutputFile")
        self.albedo_file_output.label = 'Albedo Output'
        links.new(render_layers.outputs['DiffCol'],
                  self.albedo_file_output.inputs[0])
        self.albedo_file_output.format.file_format = "PNG"
        self.albedo_file_output.format.color_mode = "RGBA"

    def __set_lights(self):
        light = bpy.data.objects["Light"]
        light.type = 'SUN'
        light.shadow_method = 'NOSHADOW'
        light.use_specular = False

    def import_obj(self, obj_path):
        self.__del_all_mesh()
        bpy.ops.import_scene.obj(filepath=obj_path)

        cur_obj = bpy.context.selected_objects[0]
        scale = 2.0 / max(cur_obj.dimensions) * 3.0
        cur_obj.scale = (scale, scale, scale)

        for polygon in cur_obj.data.polygons:
            polygon.use_smooth = True
        for mat in bpy.data.materials:
            mat.use_backface_culling = True

    def render(self):
        for output_node in [self.depth_file_output, self.normal_file_output, self.albedo_file_output]:
            output_node.base_path = ''
            
        for i in range(1):
            bpy.context.scene.render.filepath = osp.join(
                out_rgb_path, '{}.png'.format(i))
            self.depth_file_output.file_slots[0].path = osp.join(
                out_depth_path, '{}_'.format(i))
            self.normal_file_output.file_slots[0].path = osp.join(
                out_normal_path, '{}_'.format(i))
            self.albedo_file_output.file_slots[0].path = osp.join(
                out_albedo_path, '{}_'.format(i))

            bpy.ops.render.render(write_still=True)  # render still


my_render = BlenderRender()
for cate in render_cate:
    model_path = glob(
        osp.join(shapenet_path, shapenet_cate[cate], '*', 'models', '*.obj'))
    my_render.import_obj(model_path[0])
    my_render.render()
