# PANELKI_Krita_Plugin
Plugin to create and adjust basic comic panels in Krita
1. Edit Page Properties ("Настройки страницы") or Safe Area ("Безопасная область") if needed.
2. Edit number of panels ("Размерность"). Maximum 7 rows ("Ряды")/columns ("Колонки"). Gap size depends on number of panels and Page Properties (Safe Area).
3. Apply ("Применить").
4. To adjust the position of a panel select one in the Preview and make active Properties ("Настройки") tab. Use sliders.
![](https://github.com/Pull-the-lever-Kronk-WRONG-LEVAAAARR/PANELKI_Krita_Plugin/blob/main/panelki_horizi.gif)
5. To adjust the position of a group of panels select Multimanipulator (blue one) and drag sliders.
![](https://github.com/Pull-the-lever-Kronk-WRONG-LEVAAAARR/PANELKI_Krita_Plugin/blob/main/panelki_multi.gif)
6. If you are happy with the result, back to "Размерность" tab and select a mode for adding the panels to Krita: 
a) all in one layer (DEFAULT);
b) each frame is a different group (check the Divide in groups "Разбить на группы").
7. OK ("Готово").
BUGS
Gutter ("Канавка") calculations works correctly only in pixels.
Preview displays current layer correctly if you use RGBA 8-bit color space.
Color scheme of the Preview may be hard to see in some of the Krita's themes.
