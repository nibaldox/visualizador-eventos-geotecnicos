"""
Módulo para cargar y procesar archivos STL (mallas 3D) para visualización geotécnica

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np
import logging
import streamlit as st

# Librería para leer STL
from stl import mesh  # numpy-stl

logger = logging.getLogger(__name__)


class STLLoader:
    """Clase para cargar y procesar archivos STL."""

    def __init__(self) -> None:
        self.mesh: Optional[mesh.Mesh] = None
        self.vertices: Optional[np.ndarray] = None  # (N, 3)
        self.faces: Optional[np.ndarray] = None     # (M, 3) índices
        self.bounds: Optional[Tuple[float, float, float, float, float, float]] = None  # (minx,miny,minz,maxx,maxy,maxz)

    def load_stl_file(self, file_path: str) -> bool:
        """
        Cargar archivo STL desde ruta.

        Args:
            file_path: Ruta al archivo STL

        Returns:
            True si se cargó y procesó correctamente.
        """
        try:
            self.mesh = mesh.Mesh.from_file(file_path)
            self._build_geometry()
            logger.info(f"Archivo STL cargado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error al cargar STL: {e}")
            st.error(f"Error al cargar STL: {e}")
            return False

    def load_stl_from_bytes(self, file_bytes: bytes, filename: str = "uploaded.stl") -> bool:
        """
        Cargar STL desde bytes (para Streamlit uploader).

        Args:
            file_bytes: Contenido del archivo STL en bytes
            filename: Nombre del archivo (opcional)

        Returns:
            True si se cargó y procesó correctamente.
        """
        try:
            # Crear archivo temporal en memoria
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file.flush()
                
                # Cargar desde archivo temporal
                success = self.load_stl_file(tmp_file.name)
                
                # Limpiar archivo temporal
                os.unlink(tmp_file.name)
                
                if success:
                    logger.info(f"STL cargado desde bytes: {filename}")
                    
                return success
                
        except Exception as e:
            logger.error(f"Error al cargar STL desde bytes: {e}")
            st.error(f"Error al cargar STL: {e}")
            return False
    
    def load_stl_from_upload(self, uploaded_file):
        """
        Cargar archivo STL desde archivo subido por Streamlit
        
        Args:
            uploaded_file: Archivo subido desde st.file_uploader
            
        Returns:
            mesh.Mesh: Malla 3D cargada o None si hay error
        """
        try:
            if uploaded_file is None:
                return None
                
            # Leer contenido del archivo
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Resetear posición
            
            # Cargar desde bytes
            success = self.load_stl_from_bytes(file_content, uploaded_file.name)
            
            if success and self.mesh is not None:
                return self.mesh
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error al cargar STL desde upload: {str(e)}")
            st.error(f"Error al cargar archivo STL: {str(e)}")
            return None

    def export_to_obj(self, mesh_data) -> Optional[str]:
        """
        Exportar la malla como cadena en formato OBJ simple.
        
        Args:
            mesh_data: Datos de la malla STL
            
        Returns:
            Cadena con el contenido OBJ o None si no hay malla.
        """
        if mesh_data is None:
            return None
            
        try:
            lines = []
            
            # Extraer vértices únicos
            vertices = mesh_data.vectors.reshape(-1, 3)
            unique_vertices, indices = np.unique(vertices, axis=0, return_inverse=True)
            
            # Escribir vértices
            for v in unique_vertices:
                lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
            
            # Escribir caras (OBJ usa indexado basado en 1)
            faces = indices.reshape(-1, 3)
            for f in faces:
                lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")
                
            return "\n".join(lines) + "\n"
            
        except Exception as e:
            logger.error(f"Error al exportar a OBJ: {e}")
            return None

    def _build_geometry(self) -> None:
        """Construir arrays de vértices y caras a partir de la malla STL."""
        if self.mesh is None:
            self.vertices, self.faces, self.bounds = None, None, None
            return

        # self.mesh.vectors: (n_triangles, 3, 3)
        triangles = self.mesh.vectors.reshape(-1, 3)  # (n_triangles*3, 3)

        # Deduplicar vértices conservando índices para caras
        vertices_unique, inverse_idx = np.unique(triangles, axis=0, return_inverse=True)
        faces = inverse_idx.reshape(-1, 3)

        self.vertices = vertices_unique.astype(float)
        self.faces = faces.astype(int)

        # Bounds
        mins = self.vertices.min(axis=0)
        maxs = self.vertices.max(axis=0)
        self.bounds = (float(mins[0]), float(mins[1]), float(mins[2]),
                       float(maxs[0]), float(maxs[1]), float(maxs[2]))

    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la malla STL cargada."""
        if self.vertices is None or self.faces is None:
            return {}

        # Volumen mediante propiedades de masa (si disponible)
        volume = None
        cog = None
        try:
            volume, cog, _inertia = self.mesh.get_mass_properties()  # type: ignore
        except Exception:
            pass

        # Área de superficie (si disponible en numpy-stl)
        surface_area = None
        try:
            surface_area = float(np.sum(self.mesh.areas))  # type: ignore
        except Exception:
            # fallback: calcular con producto cruzado
            try:
                v0 = self.mesh.v0  # type: ignore
                v1 = self.mesh.v1  # type: ignore
                v2 = self.mesh.v2  # type: ignore
                tri_area = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)
                surface_area = float(np.sum(tri_area))
            except Exception:
                pass

        minx, miny, minz, maxx, maxy, maxz = self.bounds
        size = {
            "width": maxx - minx,
            "height": maxy - miny,
            "depth": maxz - minz,
        }

        return {
            "vertices_count": int(self.vertices.shape[0]),
            "faces_count": int(self.faces.shape[0]),
            "bounds": {
                "min": [minx, miny, minz],
                "max": [maxx, maxy, maxz],
            },
            "size": size,
            "volume": None if volume is None else float(volume),
            "center_of_gravity": None if cog is None else [float(cog[0]), float(cog[1]), float(cog[2])],
            "surface_area": surface_area,
        }


