from __future__ import division
import torch
import torchvision.transforms as transforms
import torchvision.transforms.functional_tensor as F_t
import torchvision.transforms.functional as F
import unittest
import random


class Tester(unittest.TestCase):

    def test_vflip(self):
        img_tensor = torch.randn(3, 16, 16)
        vflipped_img = F_t.vflip(img_tensor)
        vflipped_img_again = F_t.vflip(vflipped_img)
        self.assertEqual(vflipped_img.shape, img_tensor.shape)
        self.assertTrue(torch.equal(img_tensor, vflipped_img_again))

    def test_hflip(self):
        img_tensor = torch.randn(3, 16, 16)
        hflipped_img = F_t.hflip(img_tensor)
        hflipped_img_again = F_t.hflip(hflipped_img)
        self.assertEqual(hflipped_img.shape, img_tensor.shape)
        self.assertTrue(torch.equal(img_tensor, hflipped_img_again))

    def test_crop(self):
        img_tensor = torch.randint(0, 255, (3, 16, 16), dtype=torch.uint8)
        top = random.randint(0, 15)
        left = random.randint(0, 15)
        height = random.randint(1, 16 - top)
        width = random.randint(1, 16 - left)
        img_cropped = F_t.crop(img_tensor, top, left, height, width)
        img_PIL = transforms.ToPILImage()(img_tensor)
        img_PIL_cropped = F.crop(img_PIL, top, left, height, width)
        img_cropped_GT = transforms.ToTensor()(img_PIL_cropped)

        self.assertTrue(torch.equal(img_cropped, (img_cropped_GT * 255).to(torch.uint8)),
                        "functional_tensor crop not working")

    def test_adjustments(self):
        fns = ((F.adjust_brightness, F_t.adjust_brightness),
               (F.adjust_contrast, F_t.adjust_contrast),
               (F.adjust_saturation, F_t.adjust_saturation))

        for _ in range(20):
            channels = 3
            dims = torch.randint(1, 50, (2,))
            shape = (channels, dims[0], dims[1])

            if torch.randint(0, 2, (1,)) == 0:
                img = torch.rand(*shape, dtype=torch.float)
            else:
                img = torch.randint(0, 256, shape, dtype=torch.uint8)

            factor = 3 * torch.rand(1)
            for f, ft in fns:

                ft_img = ft(img, factor)
                if not img.dtype.is_floating_point:
                    ft_img = ft_img.to(torch.float) / 255

                img_pil = transforms.ToPILImage()(img)
                f_img_pil = f(img_pil, factor)
                f_img = transforms.ToTensor()(f_img_pil)

                # F uses uint8 and F_t uses float, so there is a small
                # difference in values caused by (at most 5) truncations.
                max_diff = (ft_img - f_img).abs().max()
                self.assertLess(max_diff, 5 / 255 + 1e-5)


if __name__ == '__main__':
    unittest.main()
