"""SketchUp: script Ruby que reconstruye la obra pieza a pieza.

Uso (SketchUp 2017 o posterior, incluido SketchUp Make/Free de escritorio):
  Ventana > Consola de Ruby >  load 'ruta/importar_estm.rb'
Lee piezas.json de la misma carpeta y crea un grupo por pieza (nombre = id),
una etiqueta (capa) y un material por tipo, y un diccionario de atributos
"ESTM" con tipo, masa, orden de montaje y método de fabricación. Así el
modelo se puede despiezar, filtrar por etiquetas, animar el montaje con
escenas o exportar a .skp, .dwg (Pro) o .stl.

Alternativa sin script: Archivo > Importar > modelo.dae (COLLADA).
"""

from pathlib import Path

RUBY = r'''# ESTM -> SketchUp. Generado automáticamente; ver estm/productos/sketchup.py
require 'json'
module ESTM
  COLORES = __COLORES__
  def self.importar(ruta = File.join(File.dirname(__FILE__), 'piezas.json'))
    datos = JSON.parse(File.read(ruta))
    modelo = Sketchup.active_model
    modelo.start_operation("ESTM #{datos['obra']}", true)
    raiz = modelo.active_entities.add_group
    raiz.name = "#{datos['obra']} - #{datos['nombre']}"
    datos['piezas'].each do |p|
      tipo = p['tipo']
      capa = modelo.layers[tipo] || modelo.layers.add(tipo)
      mat = modelo.materials[tipo] || modelo.materials.add(tipo)
      mat.color = Sketchup::Color.new(*(COLORES[tipo] || [170, 170, 170]))
      g = raiz.entities.add_group
      g.name = p['id']
      g.layer = capa
      g.material = mat
      pts = p['V'].map { |v| Geom::Point3d.new(v[0].m, v[1].m, v[2].m) }
      p['F'].each do |f|
        begin
          g.entities.add_face(f.map { |i| pts[i] })
        rescue ArgumentError
          # cara degenerada o no plana dentro de la tolerancia de SketchUp: se triangula
          (1...f.length - 1).each do |k|
            begin
              g.entities.add_face(pts[f[0]], pts[f[k]], pts[f[k + 1]])
            rescue ArgumentError
            end
          end
        end
      end
      %w[tipo masa_kg orden metodo].each { |k| g.set_attribute('ESTM', k, p[k]) }
    end
    raiz.set_attribute('ESTM', 'GSF', datos['equilibrio']['GSF'])
    raiz.set_attribute('ESTM', 'metodo_equilibrio', datos['equilibrio']['metodo'])
    modelo.commit_operation
    puts "ESTM: #{datos['piezas'].length} piezas importadas"
  end
end
ESTM.importar
'''


def ruby(ruta, colores):
    texto = "{" + ", ".join(f"'{t}' => [{', '.join(map(str, c))}]" for t, c in sorted(colores.items())) + "}"
    Path(ruta).write_text(RUBY.replace("__COLORES__", texto), encoding="utf-8")
    return [Path(ruta)]
