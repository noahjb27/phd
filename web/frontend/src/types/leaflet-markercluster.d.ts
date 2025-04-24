import * as L from 'leaflet';

declare module 'leaflet' {
  function markerClusterGroup(options?: MarkerClusterGroupOptions): MarkerClusterGroup;

  interface MarkerClusterGroupOptions extends L.LayerOptions {
    maxClusterRadius?: number | ((zoom: number) => number);
    iconCreateFunction?: (cluster: MarkerCluster) => L.Icon;
    clusterPane?: string;
    spiderfyOnMaxZoom?: boolean;
    showCoverageOnHover?: boolean;
    zoomToBoundsOnClick?: boolean;
    singleMarkerMode?: boolean;
    disableClusteringAtZoom?: number;
    removeOutsideVisibleBounds?: boolean;
    animate?: boolean;
    animateAddingMarkers?: boolean;
    spiderfyDistanceMultiplier?: number;
  }

  interface MarkerCluster extends L.Marker {
    getAllChildMarkers(): L.Marker[];
    getChildCount(): number;
    zoomToBounds(options?: L.FitBoundsOptions): void;
  }

  interface MarkerClusterGroup extends L.FeatureGroup {
    addLayer(layer: L.Layer): this;
    removeLayer(layer: L.Layer): this;
    clearLayers(): this;
    getLayers(): L.Layer[];
    getAllChildMarkers(): L.Marker[];
    hasLayer(layer: L.Layer): boolean;
    zoomToShowLayer(
      layer: L.Layer,
      callback?: () => void
    ): void;
  }
}
