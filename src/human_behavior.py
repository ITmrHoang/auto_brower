import asyncio
import random
import math
from typing import List, Tuple, Optional

def bezier_curve(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], num_points: int = 20) -> List[Tuple[float, float]]:
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points

async def move_mouse_humanly(page, target_x: float, target_y: float):
    try:
        start_x = target_x - random.uniform(20, 50)
        start_y = target_y - random.uniform(20, 50)

        offset_x = (target_x - start_x)
        offset_y = (target_y - start_y)
        distance = math.sqrt(offset_x**2 + offset_y**2)
        
        # Thêm lực kéo (trọng lực). Độ cong phụ thuộc vào khoảng cách (di chuyển xa thì cong nhiều hơn, gần thì ít hơn).
        # Giới hạn độ lệch tối đa là 15-25px để không bị "lượn lờ" quá đáng.
        max_deviation = min(25, distance * 0.1) 
        
        cp1_x = start_x + offset_x * random.uniform(0.2, 0.4) + random.uniform(-max_deviation, max_deviation)
        cp1_y = start_y + offset_y * random.uniform(0.2, 0.4) + random.uniform(-max_deviation, max_deviation)
        
        cp2_x = start_x + offset_x * random.uniform(0.6, 0.8) + random.uniform(-max_deviation, max_deviation)
        cp2_y = start_y + offset_y * random.uniform(0.6, 0.8) + random.uniform(-max_deviation, max_deviation)
        
        cp1 = (cp1_x, cp1_y)
        cp2 = (cp2_x, cp2_y)
        
        num_steps = 10  
        points = bezier_curve((start_x, start_y), cp1, cp2, (target_x, target_y), num_steps)
        
        for x, y in points:
            jx = x + random.uniform(-1, 1)
            jy = y + random.uniform(-1, 1)
            await page.mouse.move(jx, jy)
            await asyncio.sleep(0.002) # Rất nhanh
            
    except Exception:
        await page.mouse.move(target_x, target_y)

async def click_humanly(page, selector: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None):
    if selector:
        try:
            # Cuộn trang để đảm bảo phần tử nằm trong màn hình trước khi lấy tọa độ
            await page.locator(selector).scroll_into_view_if_needed()
            await asyncio.sleep(0.1) # Đợi một chút sau khi cuộn trang
            
            box = await page.locator(selector).bounding_box()
            if box:
                # Random click trong vùng 40% ở giữa nút (tránh mép và tránh chính tâm 0.5)
                target_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
                target_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
            else:
                await page.click(selector)
                return
        except Exception:
            try:
                await page.click(selector)
            except:
                pass
            return
    else:
        target_x = x or 0
        target_y = y or 0

    await move_mouse_humanly(page, target_x, target_y)
    await asyncio.sleep(0.01)
    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.02, 0.05))
    await page.mouse.up()

async def type_humanly(page, selector: str, text: str):
    try:
        await page.focus(selector)
        await asyncio.sleep(0.02)
        
        for char in text:
            await page.keyboard.type(char)
            delay = random.uniform(0.005, 0.02) 
            await asyncio.sleep(delay)
            
    except Exception:
        await page.fill(selector, text)
