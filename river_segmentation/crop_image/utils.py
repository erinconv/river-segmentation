import numpy
import rasterio
from rasterio.enums import Resampling as Resampling_enums
from rasterio.warp import reproject
from rasterio.warp import Resampling as Resampling_warp


def crop_image_under_from_2_images(image_under_path, image_over_path, do_ovr=True):
    image_under = rasterio.open(image_under_path)
    image_over = rasterio.open(image_over_path)
    image_under_array = image_under.read(2)
    image_over_array = image_over.read(2)
    image_over_reproject_to_under = numpy.zeros(
        image_under_array.shape, dtype=image_under_array.dtype
    )
    reproject(
        source=image_over_array,
        destination=image_over_reproject_to_under,
        src_transform=image_over.transform,
        dst_transform=image_under.transform,
        src_crs=image_under.crs,
        dst_crs=image_under.crs,
        resampling=Resampling_warp.nearest,
    )
    image_under_bad_mask = image_over_reproject_to_under > 0
    image_under.close()
    image_over.close()
    with rasterio.open(image_under_path, "r+") as dataset:
        data = dataset.read()  # Read all bands (shape: (bands, rows, cols))

        # Step 2: Apply the mask
        # Assume mask is a 2D array of the same shape as one band (rows, cols)
        # Broadcast mask to all bands if necessary
        data[:, image_under_bad_mask] = 0  # Set masked pixels to 0

        dataset.nodata = 0

        # Step 3: Write the modified data back
        dataset.write(data)

        if do_ovr:
            # Step 4: Rebuild the overviews for the .tif.ovr file
            overview_levels = [2, 4, 8, 16]  # Define reduction levels
            dataset.build_overviews(overview_levels, Resampling_enums.nearest)
            dataset.update_tags(ns="rio_overview", resampling="nearest")
