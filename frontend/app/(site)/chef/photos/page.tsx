// The food photo gallery (Django: chef/photos.html).
import type { Metadata } from "next";
import Flash from "@/components/Flash";
import { getChefPage, type ChefFormPage, type Formset } from "@/lib/api";
import ChefHero from "../ChefHero";
import PhotosForm from "./PhotosForm";

export const metadata: Metadata = { title: "Food photos - Karamu" };

export default async function Photos() {
  const { fields, photos, images, max_photos } = await getChefPage<ChefFormPage & { photos: Formset; images: string[]; max_photos: number }>("photos/");

  return (
    <>
      <ChefHero title={<>Food <span>photos</span></>}>
        Up to {max_photos} photos on your public profile. Bright, close-up shots of your dishes get the most bookings.
      </ChefHero>

      <section className="dbmain">
        <div className="container">
          <Flash />
          <PhotosForm add={fields} photos={photos} images={images} maxPhotos={max_photos} />
        </div>
      </section>
    </>
  );
}
