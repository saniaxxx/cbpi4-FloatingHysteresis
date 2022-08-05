# -*- coding: utf-8 -*-
import asyncio
from asyncio import tasks
import logging
from cbpi.api import *

@parameters([Property.Number(label="Offset_Before_50", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_Before_60", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_Before_70", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Offset_After_70", configurable=True, description="Offset below target temp when heater should switched off"),
             Property.Number(label="Boil_Threshold", configurable=True, description="When this temperature is reached, power will be set to Max Boil Output (default: 98 °C/208 F)"),
             Property.Number(label="Max_Boil_Output", configurable=True, default_value=85, description="Power when Boil Threshold is reached.")])
class FloatingHysteresis(CBPiKettleLogic):
    
    async def run(self):
        try:
            boilthreshold = 98 if self.get_config_value("TEMP_UNIT", "C") == "C" else 208
            maxtempboil = float(self.props.get("Boil_Treshold", boilthreshold))
            maxboilout = int(self.props.get("Max_Boil_Output", 100))
            offset_50 = float(self.props.get("Offset_Before_50", 0))
            offset_60 = float(self.props.get("Offset_Before_60", 0))
            offset_70 = float(self.props.get("Offset_Before_70", 0))
            offset_70plus = float(self.props.get("Offset_After_70", 0))
            kettle = self.get_kettle(self.id)
            heater = kettle.heater
            heater_actor = self.cbpi.actor.find_by_id(heater)
            logging.info("FloatingHysteresis {} {} {} {} {} {}".format(offset_50, offset_60, offset_70, offset_70plus, self.id, heater))       

            while self.running == True:
                heat_percent_old = 100
                current_kettle_power= heater_actor.power
                current_temp = self.get_sensor_value(kettle.sensor).get("value")
                target_temp = self.get_kettle_target_temp(self.id)
                if current_temp >= float(maxtempboil):
                    heat_percent = maxboilout
                else:
                    heat_percent = 100
                if (heat_percent_old != heat_percent) or (heat_percent != current_kettle_power):
                    await self.actor_set_power(heater, heat_percent)
                    heat_percent_old = heat_percent
                    
                if target_temp <= 50 and current_temp >= target_temp - offset_50:
                    await self.actor_off(heater)
                elif target_temp <= 60 and current_temp >= target_temp - offset_60:
                    await self.actor_off(heater)
                elif target_temp <= 70 and current_temp >= target_temp - offset_70:
                    await self.actor_off(heater)
                elif current_temp >= target_temp - offset_70plus:
                    await self.actor_off(heater)
                else:
                    await self.actor_on(heater)
                await asyncio.sleep(1)

        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            logging.error("FloatingHysteresis Error {}".format(e))
        finally:
            self.running = False
            await self.actor_off(self.get_kettle(self.id).heater)

def setup(cbpi):

    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server
    
    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("FloatingHysteresis", FloatingHysteresis)
