# @BEGIN data_cleaning_workflow
# @IN Menu @URI file:data/Menu.csv
# @IN MenuPage @URI file:data/MenuPage.csv
# @IN MenuItem @URI file:data/MenuItem.csv
# @IN Dish @URI file:data/Dish.csv
# @OUT Menu_final @URI file:data/Menu_cleaned.csv
# @OUT MenuPage_final @URI file:data/MenuPage_cleaned.csv
# @OUT MenuItem_final @URI file:data/MenuItem_cleaned.csv
# @OUT Dish_final @URI file:data/Dish_cleaned.csv
# @BEGIN profile_data_quality
# @IN m @AS Menu
# @IN mp @AS MenuPage
# @IN mi @AS MenuItem
# @IN d @AS Dish
# @OUT clean @AS Menu,MenuPage,MenuItem,Dish
# @END profile_data_quality
# @BEGIN clean_data_with_pandas
# @IN clean_data @AS Menu,MenuPage,MenuItem,Dish
# @OUT mp @AS MenuPage_cleaned
# @OUT mi @AS MenuItem_cleaned
# @OUT d @AS Dish_cleaned
# @OUT menu_out @AS Menu_intermediate
# @END clean_data_with_pandas
# @BEGIN fix_locations_with_openrefine
# @IN menu @AS Menu_intermediate
# @OUT cleaned_menu @AS Menu_cleaned
# @END fix_locations_with_openrefine
# @BEGIN check_ic_violations_with_sql
# @IN m @AS Menu_cleaned
# @IN mp @AS MenuPage_cleaned
# @IN mi @AS MenuItem_cleaned
# @IN d @AS Dish_cleaned
# @OUT m_out @AS Menu_final
# @OUT mp_out @AS MenuPage_final
# @OUT mi_out @AS MenuItem_final
# @OUT d_out @AS Dish_final
# @END check_ic_violations_with_sql
# @END data_cleaning_workflow


